"""
Disease & Income Normalization Module

This module provides utilities for:
1. Mapping between disease codes and full disease names
2. Extracting disease-related keywords for search refinement
3. Calculating Federal Poverty Level (FPL) percentages based on income and household size

FPL calculations are based on 2024 DHHS poverty guidelines and vary by state
(Alaska and Hawaii have higher thresholds than the lower 48 states).

Author: DuckDuckCode
"""

# Disease keywords database
# Maps full disease names to related medical terms and alternate names
# Used for grant search refinement and relevance matching
health = {
    "Heart Disease and Stroke": [
        "heart disease", "stroke", "cardiovascular", "myocardial infarction", "CVD"
    ],
    "Cancer": [
        "cancer", "tumor", "malignancy", "oncology", "breast cancer", "colorectal cancer", "skin cancer"
    ],
    "Diabetes": [
        "diabetes", "type 1", "type 2", "blood sugar", "metabolic disorder", "insulin"
    ],
    "Obesity": [
        "obesity", "overweight", "BMI", "weight management", "metabolic syndrome"
    ],
    "Alzheimer's Disease and Other Dementias": [
        "Alzheimer", "dementia", "memory loss", "neurodegenerative", "cognitive decline"
    ],
    "Arthritis": [
        "arthritis", "osteoarthritis", "rheumatoid arthritis", "joint pain", "chronic pain"
    ],
    "Chronic Kidney Disease": [
        "CKD", "kidney disease", "renal failure", "hemodialysis", "nephrology"
    ],
    "Epilepsy": [
        "epilepsy", "seizure", "neurological disorder", "convulsion", "antiepileptic drugs"
    ],
    "Tooth Decay and Oral Disease": [
        "tooth decay", "dental caries", "oral health", "cavities", "gum disease"
    ],
    "Chronic Obstructive Pulmonary Disease (COPD)": [
        "COPD", "chronic bronchitis", "emphysema", "lung disease", "respiratory disorder"
    ],
    "Depression and Other Mental Health Disorders": [
        "depression", "anxiety", "mental health", "psychiatric disorder", "bipolar disorder"
    ],
    "Hypertension": [
        "hypertension", "high blood pressure", "BP", "cardiovascular risk"
    ],
    "Asthma": [
        "asthma", "allergic respiratory", "wheezing", "inhaler", "pulmonary disorder"
    ],
    "High-Cost Drugs / Specialty Treatments": [
        "biologic", "gene therapy", "specialty drugs", "orphan disease treatments"
    ],
    "Liver Disease (including Cirrhosis and Hepatitis)": [
        "liver disease", "cirrhosis", "hepatitis", "hepatic disorder", "liver failure"
    ],
    "Multiple Sclerosis and Autoimmune Disorders": [
        "multiple sclerosis", "autoimmune", "immune disorder", "immunotherapy"
    ],
    "Serious Infectious Diseases": [
        "HIV", "tuberculosis", "antibiotic-resistant infections", "infectious disease"
    ],
    "Chronic Pain and Back Disorders": [
        "chronic pain", "back pain", "spinal disorders", "musculoskeletal pain"
    ],
    "Opioid Addiction and Substance Use Disorders": [
        "opioid", "addiction", "substance abuse", "rehabilitation", "SUD"
    ],
    "Rare or Genetic Disorders": [
        "rare disease", "genetic disorder", "inherited condition", "orphan disease"
    ]
}

# Disease code to disease name mapping
# Two-letter codes for quick reference in API requests
health_disorder_codes = {
    "HD": "Heart Disease and Stroke",
    "CA": "Cancer",
    "DB": "Diabetes",
    "OB": "Obesity",
    "AD": "Alzheimer's Disease and Other Dementias",
    "AR": "Arthritis",
    "CK": "Chronic Kidney Disease",
    "EP": "Epilepsy",
    "TD": "Tooth Decay and Oral Disease",
    "CP": "Chronic Obstructive Pulmonary Disease (COPD)",
    "MH": "Depression and Other Mental Health Disorders",
    "HT": "Hypertension",
    "AS": "Asthma",
    "SC": "High-Cost Drugs / Specialty Treatments",
    "LV": "Liver Disease (including Cirrhosis and Hepatitis)",
    "MS": "Multiple Sclerosis and Autoimmune Disorders",
    "ID": "Serious Infectious Diseases",
    "BP": "Chronic Pain and Back Disorders",
    "OA": "Opioid Addiction and Substance Use Disorders",
    "RG": "Rare or Genetic Disorders"
}

# Federal Poverty Level (FPL) thresholds for 2024
# Values represent annual income thresholds for household sizes 1-8
# Source: DHHS Poverty Guidelines 2024 (https://aspe.hhs.gov/topics/poverty-economic-mobility/poverty-guidelines)
fpl_48 = [15960, 21640, 27320, 33000, 38680, 44360, 50040, 55720]  # Lower 48 states
fpl_ak = [19950, 27050, 34150, 41250, 48350, 55450, 62550, 69650]  # Alaska (higher cost of living)
fpl_hi = [18360, 24890, 31420, 37950, 44480, 51010, 57540, 64070]  # Hawaii (higher cost of living)


def get_fpl_percentage(annual_income, household_size, state='TX'):
    """
    Calculate Federal Poverty Level (FPL) percentage for eligibility determination.
    
    The FPL percentage indicates where a household stands relative to federal poverty levels:
    - 100% FPL = at poverty line (most eligible for assistance)
    - 200% FPL = twice the poverty line
    - >200% FPL = above most grant eligibility thresholds
    
    Different states use different thresholds due to regional cost of living variations.
    
    Args:
        annual_income (float): Total annual household income in USD
        household_size (int): Number of people in the household (1-8+)
        state (str): Two-letter state code. Defaults to 'TX' (lower 48 states rates).
                     Use 'AK' for Alaska or 'HI' for Hawaii.
    
    Returns:
        float: Calculated FPL percentage (e.g., 125.5 means 125.5% of FPL)
        
    Examples:
        >>> get_fpl_percentage(40000, 4, 'TX')  # Family of 4 earning $40k in Texas
        121.2
        
        >>> get_fpl_percentage(40000, 4, 'AK')  # Same family in Alaska (higher threshold)
        96.9
    """
    # Select appropriate FPL table based on state
    table = fpl_ak if state == "AK" else fpl_hi if state == "HI" else fpl_48
    
    # Get the poverty threshold for the household size
    # Cap at index 7 (8+ people use the same threshold as 8 people)
    idx = min(household_size - 1, 7)
    threshold = table[idx]
    
    # Calculate percentage relative to poverty line
    return (annual_income / threshold) * 100


def return_keywords(key):
    """
    Retrieve disease-related keywords for grant search refinement.
    
    Takes a disease code, converts it to the full disease name, and returns
    all associated keywords for that disease. Useful for improving search
    accuracy by including medical terminology.
    
    Args:
        key (str): Two-letter disease code (e.g., 'DB' for Diabetes).
                   Case-insensitive (will be converted to uppercase).
    
    Returns:
        list: List of keywords related to the disease.
              Returns empty list if code is invalid.
              
    Examples:
        >>> return_keywords('DB')
        ['diabetes', 'type 1', 'type 2', 'blood sugar', 'metabolic disorder', 'insulin']
        
        >>> return_keywords('invalid')
        []
    """
    # Look up disease name from code, then get keywords for that disease
    return health.get(health_disorder_codes.get(key.upper()), [])