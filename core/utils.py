from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import requests
import io
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_url):
    """
    Downloads a PDF from a URL and extracts its text.
    """
    if not pdf_url:
        return ""
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        with io.BytesIO(response.content) as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text from {pdf_url}: {e}")
        return ""

def calculate_similarity_score(job_skills, job_description, candidate_data, resume_text=""):
    """
    Calculates a similarity score between job requirements and candidate profile.
    Considers both explicit skills and the broader job description (JD).
    
    Args:
        job_skills (str): Comma separated skills required.
        job_description (str): Full text of the job description (often contains context).
        candidate_data (str): Combined text of candidate skills and projects.
        resume_text (str): Text extracted from resume.
        
    Returns:
        float: Score between 0 and 100.
    """
    if not job_skills and not job_description:
        return 0.0
    if not candidate_data and not resume_text:
        return 0.0
        
    candidate_full_text = f"{candidate_data} {resume_text}".strip().lower()
    
    def get_match_stats(target_text, candidate_text):
        """Helper to get keyword and semantic scores for a specific target."""
        if not target_text:
            return 0.0, 0.0
            
        # 1. Keyword Overlap
        skills_list = [s.strip().lower() for s in target_text.replace('\n', ' ').split(',') if s.strip()]
        if not skills_list:
            # Fallback for descriptions: extract meaningful words or just use semantic
            keyword_score = 0.0
        else:
            match_count = 0
            for skill in skills_list:
                if skill in candidate_text:
                    match_count += 1
            keyword_score = (match_count / len(skills_list)) * 100

        # 2. Semantic (TF-IDF)
        try:
            documents = [target_text.lower(), candidate_text]
            tfidf = TfidfVectorizer(stop_words='english', ngram_range=(1, 3))
            tfidf_matrix = tfidf.fit_transform(documents)
            semantic_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
        except:
            semantic_score = keyword_score
            
        return keyword_score, semantic_score

    # Score against explicit SKILLS (Primary weight)
    skills_kw, skills_sem = get_match_stats(job_skills, candidate_full_text)
    # Weighted skills score: 60% Keyword / 40% Semantic (Keywords are king here)
    final_skills_score = (skills_kw * 0.6) + (skills_sem * 0.4) if job_skills else 0.0

    # Score against JOB DESCRIPTION (Contextual weight)
    # We treat JD mainly semantically but look for implicit keywords
    jd_clean = job_description.replace('<p>', ' ').replace('</p>', ' ').replace('<br>', ' ') # Simple HTML strip
    jd_kw, jd_sem = get_match_stats(jd_clean, candidate_full_text)
    # Weighted JD score: 30% Keyword / 70% Semantic (Breadth matters more here)
    final_jd_score = (jd_kw * 0.3) + (jd_sem * 0.7) if job_description else 0.0

    # BLENDED FINAL SCORE
    # If skills are provided, they take 80% weight. If only JD is provided, JD takes 100%.
    if job_skills and job_description:
        final_score = (final_skills_score * 0.8) + (final_jd_score * 0.2)
    elif job_skills:
        final_score = final_skills_score
    else:
        final_score = final_jd_score
    
    return round(min(100.0, final_score), 2)
