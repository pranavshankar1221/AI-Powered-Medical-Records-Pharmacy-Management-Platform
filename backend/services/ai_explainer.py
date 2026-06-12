"""
AI-powered medicine explanation service.
Converts medical information into patient-friendly language.

SAFETY RULES:
- Never diagnoses diseases
- Never modifies dosage
- Never prescribes medicines
- Only explains existing database information
"""

import config

DISCLAIMER = "This information is for awareness only. Follow your doctor's prescription."

# Pre-built explanation templates for common categories
CATEGORY_TEMPLATES = {
    "Analgesic": "This medicine is commonly used to help reduce pain and discomfort.",
    "Antipyretic": "This medicine is commonly used to help reduce fever.",
    "Antibiotic": "This medicine is an antibiotic that helps your body fight bacterial infections.",
    "Antacid": "This medicine helps neutralize stomach acid and may relieve heartburn or indigestion.",
    "Antihistamine": "This medicine is commonly used to help relieve allergy symptoms.",
    "Anti-inflammatory": "This medicine helps reduce inflammation and associated pain or swelling.",
    "Antihypertensive": "This medicine is used to help manage blood pressure levels.",
    "Antidiabetic": "This medicine is used to help manage blood sugar levels.",
    "Bronchodilator": "This medicine helps open up the airways in your lungs to make breathing easier.",
    "Vitamin": "This is a nutritional supplement that provides essential vitamins to support your health.",
}


def generate_simple_explanation(medicine_name: str, purpose: str = "",
                                 category: str = "", side_effects: str = "") -> str:
    """
    Generate a patient-friendly explanation without using external AI.
    Falls back to this if Gemini API is not configured.
    """
    parts = []

    # Medicine name intro
    parts.append(f"**{medicine_name}**")

    # Category-based explanation
    if category and category in CATEGORY_TEMPLATES:
        parts.append(CATEGORY_TEMPLATES[category])
    elif purpose:
        parts.append(f"This medicine is commonly used for: {purpose}")
    else:
        parts.append("This medicine has been prescribed by your doctor for your specific condition.")

    # Side effects awareness
    if side_effects:
        parts.append(f"\n⚠️ **Possible side effects to be aware of:** {side_effects}")
        parts.append("If you experience severe side effects, contact your doctor immediately.")

    parts.append(f"\n📋 *{DISCLAIMER}*")

    return "\n\n".join(parts)


async def generate_ai_explanation(medicine_name: str, purpose: str = "",
                                   category: str = "", side_effects: str = "",
                                   dosage_schedule: str = "", food_instructions: str = "") -> str:
    """
    Generate AI-powered patient-friendly explanation using Gemini API.
    Falls back to template-based explanation if API key is not set.
    """
    if not config.GEMINI_API_KEY:
        return generate_simple_explanation(medicine_name, purpose, category, side_effects)

    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)

        prompt = f"""You are a pharmacy assistant helping patients understand their medicines.
Convert the following medical information into simple, patient-friendly language.

STRICT RULES:
- Do NOT diagnose any disease
- Do NOT recommend changing dosage
- Do NOT prescribe any new medicines
- ONLY explain what the medicine is commonly used for
- Use simple, everyday language
- Be reassuring but factual

Medicine: {medicine_name}
Category: {category or 'N/A'}
Purpose: {purpose or 'N/A'}
Common Side Effects: {side_effects or 'None listed'}
Dosage Schedule: {dosage_schedule or 'As prescribed by doctor'}
Food Instructions: {food_instructions or 'N/A'}

Please provide a brief, friendly explanation (3-4 sentences max) about this medicine.
End with: "Always follow your doctor's prescription."
"""

        response = model.generate_content(prompt)
        explanation = response.text.strip()

        # Always append disclaimer
        return f"{explanation}\n\n📋 *{DISCLAIMER}*"

    except Exception as e:
        # Fallback to simple explanation on any error
        return generate_simple_explanation(medicine_name, purpose, category, side_effects)


def generate_prescription_summary_simple(medicines: list) -> str:
    if not medicines:
        return "No medicines to summarize."

    names = [m.get("medicine_name", "Unknown") for m in medicines]
    purposes = [m.get("purpose", "") for m in medicines if m.get("purpose")]

    summary_parts = [
        "📋 **Your Prescription Summary**\n",
        f"You have been prescribed {len(names)} medicine(s): {', '.join(names)}.",
    ]

    if purposes:
        summary_parts.append(
            f"\nThese medicines are commonly used for: {'; '.join(set(purposes))}."
        )

    summary_parts.append(
        "\n⏰ Please take your medicines as directed by your doctor."
    )
    summary_parts.append(f"\n*{DISCLAIMER}*")

    return "\n".join(summary_parts)


def generate_prescription_summary(medicines: list) -> str:
    """
    Generate a patient-friendly summary of all medicines in a bill.
    """
    if not medicines:
        return "No medicines to summarize."

    if not config.GEMINI_API_KEY:
        return generate_prescription_summary_simple(medicines)

    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)

        med_details = []
        for m in medicines:
            name = m.get('medicine_name', 'Unknown')
            purpose = m.get('purpose', 'N/A')
            dosage = m.get('dosage_instructions', 'As prescribed')
            med_details.append(f"- {name} (Purpose: {purpose}, Dosage: {dosage})")
            
        meds_text = "\n".join(med_details)

        prompt = f"""You are a helpful pharmacy assistant. A patient has been prescribed the following medicines:
{meds_text}

Please provide a concise, patient-friendly summary (4-6 sentences) explaining what this combination of medicines is generally meant to treat, and highlight any important scheduling or general advice based on the dosages. 
STRICT RULES:
- Do NOT diagnose any disease
- Do NOT recommend changing dosage
- Do NOT prescribe any new medicines
- Use simple, reassuring language

End with: "Always follow your doctor's prescription."
"""

        response = model.generate_content(prompt)
        explanation = response.text.strip()

        return f"📋 **Your AI Prescription Summary**\n\n{explanation}\n\n*{DISCLAIMER}*"
    except Exception as e:
        return generate_prescription_summary_simple(medicines)
