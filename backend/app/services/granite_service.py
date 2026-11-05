"""
IBM Granite (watsonx.ai) service – text generation & NLP tasks.
"""
import logging
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("grant_finder.granite")

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
WATSONX_GENERATE_URL = "{base}/ml/v1/text/generation?version=2023-05-29"


class GraniteService:
    """Wrapper around IBM watsonx.ai REST API for Granite models."""

    def __init__(self):
        self._iam_token: Optional[str] = None

    # ── Authentication ─────────────────────────────────────────────────────────

    async def _get_iam_token(self) -> str:
        """Fetch a fresh IAM bearer token from IBM Cloud."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                IAM_TOKEN_URL,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": settings.ibm_watsonx_api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            self._iam_token = resp.json()["access_token"]
            return self._iam_token

    # ── Core Generation ────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 800,
        temperature: float = 0.3,
        stop_sequences: Optional[list] = None,
    ) -> str:
        """Call IBM Granite text generation endpoint."""
        token = await self._get_iam_token()
        url = WATSONX_GENERATE_URL.format(base=settings.ibm_watsonx_url)

        payload = {
            "model_id": settings.ibm_granite_model_id,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "repetition_penalty": 1.1,
            },
            "project_id": settings.ibm_watsonx_project_id,
        }
        if stop_sequences:
            payload["parameters"]["stop_sequences"] = stop_sequences

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["results"][0]["generated_text"].strip()

    # ── NLP Tasks ──────────────────────────────────────────────────────────────

    async def extract_eligibility(self, grant_text: str) -> dict:
        """
        Use Granite to extract structured eligibility criteria from raw grant text.
        Returns a dict with keys: stages, domains, locations, requirements, min_funding, max_funding.
        """
        prompt = f"""You are an expert grant analyst. Extract eligibility criteria from the following grant description.
Return a JSON object with these keys:
- "stages": list of applicable startup stages (idea/prototype/mvp/early_stage/growth/scale)
- "domains": list of applicable industry domains (e.g. EdTech, HealthTech, AgriTech)
- "locations": list of states or countries required
- "requirements": list of specific requirements (e.g. "DPIIT registered", "< 3 years old")
- "min_funding": minimum funding amount as number or null
- "max_funding": maximum funding amount as number or null
- "currency": currency code (INR/USD) or null

Grant Text:
\"\"\"
{grant_text[:3000]}
\"\"\"

Return ONLY valid JSON, no explanation:"""

        try:
            result = await self.generate(prompt, max_new_tokens=400, temperature=0.1)
            import json
            # Strip markdown code fences if present
            result = result.strip().strip("```json").strip("```").strip()
            return json.loads(result)
        except Exception as e:
            logger.warning(f"Eligibility extraction failed: {e}")
            return {"stages": [], "domains": [], "locations": [], "requirements": [], "min_funding": None, "max_funding": None}

    async def compute_match_score(
        self, startup_profile: dict, grant_info: dict
    ) -> tuple[float, str, list, list]:
        """
        Use Granite to compute a match score (0-100) between a startup and a grant.
        Returns (score, explanation, missing_criteria, strong_matches).
        """
        prompt = f"""You are a grant matching expert. Evaluate how well this startup matches the grant.

Startup Profile:
{startup_profile}

Grant Information:
{grant_info}

Provide:
1. A match score from 0 to 100 (integer)
2. A brief explanation (2-3 sentences)
3. List of matching strengths
4. List of missing or weak criteria

Respond in this exact JSON format:
{{
  "score": <integer 0-100>,
  "explanation": "<explanation>",
  "strong_matches": ["<item1>", "<item2>"],
  "missing_criteria": ["<item1>", "<item2>"]
}}

Return ONLY valid JSON:"""

        try:
            result = await self.generate(prompt, max_new_tokens=500, temperature=0.2)
            import json
            result = result.strip().strip("```json").strip("```").strip()
            data = json.loads(result)
            return (
                float(data.get("score", 0)),
                data.get("explanation", ""),
                data.get("missing_criteria", []),
                data.get("strong_matches", []),
            )
        except Exception as e:
            logger.warning(f"Match score computation failed: {e}")
            return (0.0, "Unable to compute match score.", [], [])

    async def generate_proposal(
        self,
        startup_profile: dict,
        grant_info: dict,
        additional_context: str = "",
    ) -> str:
        """
        Generate a tailored grant proposal draft using IBM Granite.
        """
        context_section = f"\nAdditional Context:\n{additional_context}" if additional_context else ""

        prompt = f"""You are an expert grant writer helping a startup apply for funding.
Write a professional grant application proposal draft.

Startup Profile:
- Name: {startup_profile.get('name')}
- Domain: {startup_profile.get('domain')}
- Stage: {startup_profile.get('stage')}
- Description: {startup_profile.get('description', 'N/A')}
- Location: {startup_profile.get('location_state', '')}, {startup_profile.get('location_country', 'India')}
- DPIIT Recognized: {startup_profile.get('dpiit_recognized', False)}
- Keywords: {', '.join(startup_profile.get('keywords', []))}

Grant Details:
- Title: {grant_info.get('title')}
- Provider: {grant_info.get('provider')}
- Description: {grant_info.get('description', 'N/A')}
- Requirements: {', '.join(grant_info.get('requirements', []))}
- Funding: {grant_info.get('funding_amount_min', 'N/A')} – {grant_info.get('funding_amount_max', 'N/A')} {grant_info.get('funding_currency', 'INR')}
{context_section}

Write a structured proposal with the following sections:
1. Executive Summary
2. Problem Statement
3. Proposed Solution
4. Innovation & Technology
5. Market Opportunity
6. Team & Capacity
7. Budget Justification
8. Expected Impact
9. Conclusion

Use professional language. Keep the proposal factual and compelling:"""

        return await self.generate(prompt, max_new_tokens=1500, temperature=0.4)


# Singleton instance
granite_service = GraniteService()
