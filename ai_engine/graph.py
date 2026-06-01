import os
import json
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    industry: str
    location: str
    company_size: str
    target_audience: str
    raw_search_data: str
    extracted_leads: List[dict]
    final_qualified_leads: List[dict]

class LeadExtraction(BaseModel):
    company_name: str = Field(description="Name of the company")
    website_url: str = Field(description="Website URL if found, else empty string")
    location: str = Field(description="Location of the company")
    description: str = Field(description="Brief summary of what the company does")

class ExtractionOutput(BaseModel):
    leads: List[LeadExtraction]

class Qualification(BaseModel):
    score: str = Field(description="Qualification score: High, Medium, or Low", enum=["High", "Medium", "Low"])
    reasoning: str = Field(description="Analytical reasoning statement for the score based on ICP")

def get_llm():
    api_key = os.environ.get("OPENROUTER_API_KEY", "dummy-key")
    base_url = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    model_name = os.environ.get("LLM_MODEL", "meta-llama/llama-3-8b-instruct")
    
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.0
    )

def discovery_node(state: AgentState):
    """Executes a search string matching user inputs to aggregate fragments."""
    # Targeted query excluding popular aggregator sites
    query = f"{state['industry']} company {state['location']} -site:clutch.co -site:goodfirms.co -site:glassdoor.com"
    
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=20))
            
        raw_results = "\n\n".join([f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}" for r in results])
    except Exception as e:
        raw_results = f"Search failed: {e}"
        
    return {"raw_search_data": raw_results}

def extraction_node(state: AgentState):
    """Maps raw search results into structured corporate details."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(ExtractionOutput)
    
    prompt = f"""
    You are an expert B2B lead researcher. Extract ACTUAL business entities from the search results below.
    CRITICAL INSTRUCTIONS:
    - IGNORE directory sites, aggregators, job boards, or review sites (e.g., Clutch, GoodFirms, Glassdoor, LinkedIn directories, Enterprise League, Vendorland, etc.).
    - ONLY extract the actual companies that provide the services or fit the industry.
    - Extract as many valid companies as you can find.
    
    Search Results:
    {state['raw_search_data']}
    """
    
    try:
        output = structured_llm.invoke(prompt)
        leads = [lead.model_dump() for lead in output.leads] if output and output.leads else []
    except Exception as e:
        print(f"Extraction failed: {e}")
        leads = []
        
    return {"extracted_leads": leads}

def qualification_node(state: AgentState):
    """Cross-references extracted descriptions against ICP and scores them."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(Qualification)
    
    icp_description = (
        f"Industry: {state['industry']}, Location: {state['location']}, "
        f"Size: {state['company_size']}, Audience: {state['target_audience']}"
    )
    
    qualified_leads = []
    
    for lead in state["extracted_leads"]:
        prompt = f"""
        Evaluate if this company fits the Ideal Customer Profile (ICP).
        ICP: {icp_description}
        
        Company Profile:
        Name: {lead['company_name']}
        Description: {lead['description']}
        
        Score as High, Medium, or Low match. Provide a concise 1-sentence reasoning.
        """
        try:
            qual = structured_llm.invoke(prompt)
            lead["qualification_score"] = qual.score
            lead["reasoning"] = qual.reasoning
        except Exception as e:
            print(f"Qualification failed for {lead['company_name']}: {e}")
            lead["qualification_score"] = "Low"
            lead["reasoning"] = "Failed to evaluate due to LLM error."
            
        qualified_leads.append(lead)
        
    return {"final_qualified_leads": qualified_leads}

def database_node(state: AgentState):
    """Saves finalized objects to the Django database."""
    from scraper.models import ScrapedLead
    
    for lead in state["final_qualified_leads"]:
        ScrapedLead.objects.create(
            company_name=lead["company_name"],
            website_url=lead["website_url"],
            location=lead.get("location", state["location"]),
            industry=state["industry"],
            description_summary=lead["description"],
            qualification_score=lead["qualification_score"],
            pipeline_status="New",
            reasoning=lead["reasoning"]
        )
        
    return {}

# Build the Graph
workflow = StateGraph(AgentState)
workflow.add_node("discovery", discovery_node)
workflow.add_node("extraction", extraction_node)
workflow.add_node("qualification", qualification_node)
workflow.add_node("database", database_node)

workflow.set_entry_point("discovery")
workflow.add_edge("discovery", "extraction")
workflow.add_edge("extraction", "qualification")
workflow.add_edge("qualification", "database")
workflow.add_edge("database", END)

lead_gen_app = workflow.compile()

def run_lead_gen(industry: str, location: str, company_size: str, target_audience: str):
    """Helper function to run the compiled graph synchronously."""
    initial_state = {
        "industry": industry,
        "location": location,
        "company_size": company_size,
        "target_audience": target_audience,
        "raw_search_data": "",
        "extracted_leads": [],
        "final_qualified_leads": []
    }
    result = lead_gen_app.invoke(initial_state)
    return result
