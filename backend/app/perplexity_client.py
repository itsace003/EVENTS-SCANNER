import httpx
import asyncio
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import structlog

logger = structlog.get_logger()

class PerplexityClient:
    """
    Advanced Perplexity API client for AI event discovery and classification.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key is required. Set PERPLEXITY_API_KEY environment variable.")
        
        self.base_url = "https://api.perplexity.ai"
        self.model = "sonar-pro"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Event-Scanner/2.0"
        }
        self._cache = {}
    
    async def search_events(self, location: str, platform: str = "luma", date_range: str = "next 30 days") -> List[Dict[str, Any]]:
        """
        Search for AI-related events using Perplexity's search capabilities.
        """
        search_queries = self._generate_search_queries(location, platform, date_range)
        all_events = []
        
        for query in search_queries:
            try:
                events = await self._execute_search(query, platform)
                all_events.extend(events)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error("Search query failed", query=query, error=str(e))
                continue
        
        # Deduplicate events
        unique_events = self._deduplicate_events(all_events)
        
        # Classify and score events
        classified_events = []
        for event in unique_events:
            try:
                classification = await self.classify_event(event)
                if classification["ai_relevance_score"] >= 5:  # Only include relevant events
                    event.update(classification)
                    classified_events.append(event)
            except Exception as e:
                logger.error("Event classification failed", event=event.get("title"), error=str(e))
                continue
        
        return classified_events
    
    async def classify_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an event's AI relevance and categorize it.
        """
        cache_key = f"classify_{hash(str(event_data.get('title', '')))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        classification_prompt = self._build_classification_prompt(event_data)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are an AI event classifier. Analyze the provided event data and return a JSON response with:
                            1. ai_relevance_score: Integer 1-10 (1=not AI related, 10=highly AI focused)
                            2. category: One of ["Conference", "Workshop", "Networking", "Talk", "Hackathon", "Other"]
                            3. tags: Array of relevant tags like ["beginner-friendly", "technical", "startup", "research", etc.]
                            4. event_type: "online", "in-person", or "hybrid"
                            5. reasoning: Brief explanation of the scoring
                            
                            Only respond with valid JSON."""
                        },
                        {
                            "role": "user",
                            "content": classification_prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Parse JSON response
                try:
                    classification = json.loads(content)
                    self._cache[cache_key] = classification
                    return classification
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    logger.warning("Failed to parse classification JSON", content=content)
                    return {
                        "ai_relevance_score": 5,
                        "category": "Other",
                        "tags": [],
                        "event_type": "unknown",
                        "reasoning": "Classification parsing failed"
                    }
                
        except Exception as e:
            logger.error("Classification request failed", error=str(e))
            raise
    
    async def _execute_search(self, query: str, platform: str) -> List[Dict[str, Any]]:
        """
        Execute a search query using Perplexity.
        """
        search_prompt = f"""
        Search for AI-related events on {platform}.com with the following criteria: {query}
        
        For each event found, extract and return the following information in a structured format:
        - Title
        - Description (if available)
        - Date and time
        - Location (or "Online" if virtual)
        - Event URL
        - Organizer name
        - Price (if mentioned)
        
        Focus on events happening in the next 30 days. Return the information as a JSON array.
        """
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI event researcher. Search for and extract structured event information. Return only valid JSON arrays."
                        },
                        {
                            "role": "user",
                            "content": search_prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2000
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Parse the JSON response
                try:
                    events = json.loads(content)
                    if isinstance(events, list):
                        return events
                    else:
                        return [events] if isinstance(events, dict) else []
                except json.JSONDecodeError:
                    logger.warning("Failed to parse search results JSON", content=content[:200])
                    return []
                
        except Exception as e:
            logger.error("Search execution failed", query=query, error=str(e))
            return []
    
    def _generate_search_queries(self, location: str, platform: str, date_range: str) -> List[str]:
        """
        Generate diverse search queries for comprehensive event discovery.
        """
        base_queries = [
            f"AI events {location} {date_range}",
            f"artificial intelligence conferences {location}",
            f"machine learning workshops {location}",
            f"AI startup events {location}",
            f"tech AI meetups {location}",
            f"deep learning talks {location}",
            f"AI networking events {location}",
            f"generative AI events {location}"
        ]
        
        return base_queries
    
    def _build_classification_prompt(self, event_data: Dict[str, Any]) -> str:
        """
        Build a comprehensive prompt for event classification.
        """
        title = event_data.get("title", "")
        description = event_data.get("description", "")
        organizer = event_data.get("organizer", "")
        location = event_data.get("location", "")
        
        return f"""
        Event Details:
        Title: {title}
        Description: {description}
        Organizer: {organizer}
        Location: {location}
        
        Please analyze this event and classify it according to its AI relevance and characteristics.
        """
    
    def _deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate events based on title and date similarity.
        """
        unique_events = []
        seen_events = set()
        
        for event in events:
            # Create a signature for the event
            title = event.get("title", "").lower().strip()
            date_str = str(event.get("date_time", ""))
            signature = f"{title}_{date_str}"
            
            if signature not in seen_events:
                seen_events.add(signature)
                unique_events.append(event)
        
        return unique_events