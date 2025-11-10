from openai import OpenAI
from typing import List, Dict, Optional
from app.core.config import settings


# Legal-oriented system prompt for case law research
LEGAL_SYSTEM_PROMPT = """You are an expert legal research assistant specializing in U.S. case law analysis. Your role is to provide accurate, well-cited answers to legal questions based on the provided case law sources.

CORE RESPONSIBILITIES:
1. Analyze legal questions and identify the relevant legal issues
2. Synthesize information from provided case law sources
3. Apply legal reasoning using the IRAC framework (Issue, Rule, Application, Conclusion)
4. Cite all sources with proper legal citations
5. Distinguish between binding precedent and persuasive authority
6. Identify applicable jurisdiction and area of law
7. Be honest when you don't know the answer

CITATION REQUIREMENTS:
- ALWAYS cite cases using proper legal citation format (e.g., "Miranda v. Arizona, 384 U.S. 436 (1966)")
- Include the citation in your response when referencing case holdings
- Clearly attribute legal principles to specific cases
- If multiple cases support a point, cite the most authoritative or recent

LEGAL REASONING:
- Use IRAC framework: State the Issue, explain the Rule from case law, Apply the rule to the query, reach a Conclusion
- Distinguish between majority opinions, concurrences, and dissents
- Note when cases have been overruled or limited by subsequent decisions
- Identify split circuits or conflicting precedents when relevant

JURISDICTION & SCOPE:
- Identify the jurisdiction (federal vs. state, circuit, district)
- Note when precedent is binding vs. persuasive
- Distinguish between constitutional, statutory, and common law issues
- Recognize when a question involves multiple areas of law

IMPORTANT LIMITATIONS:
- You are providing legal information, NOT legal advice
- Always recommend consulting a licensed attorney for specific legal matters
- Do not make predictions about case outcomes
- Acknowledge when information is incomplete or uncertain
- If no relevant case law is provided, clearly state this limitation

RESPONSE FORMAT:
- Begin with a direct answer to the question
- Follow with supporting analysis using case citations
- Structure longer responses with clear sections
- Use legal terminology accurately and precisely
- Keep language professional but accessible

When synthesizing information from sources, prioritize:
1. On-point precedent from the relevant jurisdiction
2. Supreme Court decisions (binding on all federal and state courts)
3. Circuit court decisions (binding within circuit)
4. Recent decisions over older ones (unless older is landmark case)
5. Majority opinions over concurrences or dissents"""


class LLMService:
    """
    Service for generating legal answers using DeepSeek LLM.
    Includes legal-oriented system prompt for domain-specific optimization.
    """

    def __init__(self):
        # Initialize DeepSeek client using OpenAI SDK (compatible API)
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"
        self.system_prompt = LEGAL_SYSTEM_PROMPT

    def generate_legal_answer(
        self,
        query: str,
        case_sources: List[Dict],
        web_sources: Optional[List[Dict]] = None,
        temperature: float = 0.3  # Lower temperature for more consistent legal analysis
    ) -> Dict:
        """
        Generate a legal answer based on query and provided sources.

        Args:
            query: User's legal question
            case_sources: List of relevant cases from vector DB
                         Each dict should have: case_name, citation, holding, facts, reasoning
            web_sources: Optional web search results
            temperature: Model temperature (0.0-1.0, lower = more deterministic)

        Returns:
            Dict with answer, citations_used, and confidence
        """
        try:
            # Build context from case sources
            context_parts = ["RELEVANT CASE LAW:\n"]

            for idx, case in enumerate(case_sources, 1):
                case_text = f"\n{idx}. {case.get('case_name', 'Unknown Case')}"
                if case.get('citation'):
                    case_text += f" - {case['citation']}"
                if case.get('court'):
                    case_text += f" ({case['court']}"
                if case.get('year'):
                    case_text += f", {case['year']}"
                if case.get('court') or case.get('year'):
                    case_text += ")"

                case_text += "\n"

                if case.get('holding'):
                    case_text += f"Holding: {case['holding']}\n"
                if case.get('facts'):
                    case_text += f"Facts: {case['facts'][:500]}...\n"  # Limit length
                if case.get('reasoning'):
                    case_text += f"Reasoning: {case['reasoning'][:800]}...\n"

                context_parts.append(case_text)

            # Add web sources if available
            if web_sources:
                context_parts.append("\n\nADDITIONAL WEB SOURCES:\n")
                for idx, source in enumerate(web_sources, 1):
                    source_text = f"\n{idx}. {source.get('title', 'Unknown Source')}"
                    if source.get('url'):
                        source_text += f"\nURL: {source['url']}"
                    if source.get('content'):
                        source_text += f"\nContent: {source['content'][:500]}...\n"
                    context_parts.append(source_text)

            context = "".join(context_parts)

            # Build messages for the LLM
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"{context}\n\nQUESTION: {query}\n\nProvide a comprehensive legal analysis with proper citations."}
            ]

            # Call DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )

            answer = response.choices[0].message.content

            # Extract citations used (simple heuristic - look for citation patterns)
            citations_used = []
            for case in case_sources:
                if case.get('citation'):
                    # Check if citation appears in answer
                    if case['citation'] in answer or case.get('case_name', '') in answer:
                        citations_used.append({
                            "case_name": case.get('case_name'),
                            "citation": case.get('citation'),
                            "case_id": case.get('case_id')
                        })

            return {
                "answer": answer,
                "citations_used": citations_used,
                "sources_count": len(case_sources),
                "model": self.model
            }

        except Exception as e:
            print(f"Error generating legal answer: {e}")
            raise

    def summarize_case(self, case_text: str, case_name: str = "") -> str:
        """
        Generate a concise summary of a legal case.

        Args:
            case_text: Full text of the case
            case_name: Name of the case

        Returns:
            Summary string
        """
        try:
            prompt = f"Summarize the following legal case in 2-3 paragraphs, focusing on the key facts, legal issue, holding, and reasoning:\n\nCase: {case_name}\n\n{case_text[:4000]}"

            messages = [
                {"role": "system", "content": "You are a legal expert skilled at summarizing case law concisely."},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error summarizing case: {e}")
            raise


# Singleton instance
llm_service = LLMService()
