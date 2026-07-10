###############################################
# Supply your OpenAI API key and Entrez email #
###############################################

import pandas as pd
from datetime import datetime
from Bio import Entrez
import xml.etree.ElementTree as ET
import csv
import json
import os
import re
from openai import OpenAI
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'supply_your_own_key')
client = OpenAI(api_key=OPENAI_API_KEY)
Entrez.email = os.environ.get("ENTREZ_EMAIL", "your_entrez_email")

RUNDATE = datetime.now().strftime("%Y%m%d")
write_dir = f"Output/output_raw_{RUNDATE}/"
if not os.path.exists(write_dir):
    os.makedirs(write_dir)
consolidate_output_dir = "Output/output_consolidate/"
if not os.path.exists(consolidate_output_dir):
    os.makedirs(consolidate_output_dir)


def remove_namespace(xml):
    """Remove namespace from the parsed XML."""
    for elem in xml.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return xml


def search_pubmed(query, retmax=10):
    # Search PubMed with increased retmax
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_publication_year(pmid):
    """Fetch the publication year of the article."""
    handle = Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="xml")
    xml_data = handle.read()
    handle.close()

    root = ET.fromstring(xml_data)
    root = remove_namespace(root)

    # Find the publication date in the PubMed XML data
    pub_year = root.find('.//PubDate/Year')
    if pub_year is not None:
        return pub_year.text

    # Alternative tags to look for in case 'Year' tag is not found
    medline_date = root.find('.//PubDate/MedlineDate')
    if medline_date is not None:
        return medline_date.text.split()[0]  # Take only the year if it's a full date
    return None


def fetch_full_text(pmid):
    try:
        handle = Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid)
        record = Entrez.read(handle)
        handle.close()

        # Debugging: Check the elink result for the given PMID
        # print(f"Elink result for PMID {pmid}: {record}")

        # Check if this is just a reference link and not a full-text PMC link
        if not record[0]['LinkSetDb'] or record[0]['LinkSetDb'][0]['LinkName'] == 'pubmed_pmc_refs':
            print(f"No full-text PMC ID found for PMID {pmid}, only references.")
            return None  # No full text available in PMC

        pmc_id = record[0]['LinkSetDb'][0]['Link'][0]['Id']

        handle = Entrez.efetch(db="pmc", id=pmc_id, rettype="full", retmode="xml")
        # article = ET.parse(handle)
        xml_data = handle.read()
        handle.close()

        # Parse the XML
        root = ET.fromstring(xml_data)
        # Remove namespaces
        root = remove_namespace(root)

        # Find the body of the article
        body = root.find('.//body')
        if body is None:
            return None

        full_text = ""

        # Define section titles to exclude
        excluded_sections = ['references', 'acknowledgments', 'supplementary', 'funding', 'footnotes']

        # Iterate over sections in the body
        for sec in body.findall('.//sec'):
            # Get the title of the section
            sec_title_elem = sec.find('title')
            if sec_title_elem is not None:
                sec_title = sec_title_elem.text.lower() if sec_title_elem.text else ''
                # Skip sections like 'References', 'Acknowledgments', etc.
                if any(excluded in sec_title for excluded in excluded_sections):
                    continue
            # Extract paragraphs in the section
            for p in sec.findall('.//p'):
                paragraph_text = ''.join(p.itertext())
                full_text += paragraph_text.strip() + '\n\n'
        # Also, handle paragraphs directly under body (not within a section)
        for p in body.findall('./p'):
            paragraph_text = ''.join(p.itertext())
            full_text += paragraph_text.strip() + '\n\n'

        return full_text.strip() if full_text else None  # Return None if no full text found

    except Exception as e:
        print(f"Error fetching full text for PMID {pmid}: {str(e)}")
        return None


def fetch_full_texts(query, num_articles=2):
    pmids = search_pubmed(query, retmax=num_articles * 10)  # Get more PMIDs than needed
    full_texts = []

    print('pmids', pmids)
    for pmid in pmids:
        if len(full_texts) >= num_articles:
            break

        full_text = fetch_full_text(pmid)
        pub_year = fetch_publication_year(pmid)

        if full_text:
            full_texts.append((pmid, pub_year, full_text))

    return full_texts


# Define the base URL for the PMC E-Utilities API
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_article_type(pmid, retry_count=3):
    """
    Fetch the article type for a given PMID using the PMC API.
    :param pmid: The PMID of the article
    :param retry_count: Number of retries for handling rate limits
    :return: A list of publication types or "Unknown"
    """
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
        "rettype": "abstract"
    }

    for attempt in range(retry_count):
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()

            # Parse the XML response
            root = ET.fromstring(response.content)
            publication_types = [ptype.text for ptype in root.findall(".//PublicationType")]

            # Return all publication types or "Unknown" if none found
            return "; ".join(publication_types) if publication_types else "Unknown"

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and attempt < retry_count - 1:
                print(f"Rate limit hit for PMID {pmid}. Retrying...")
                time.sleep(5)  # Wait before retrying
            else:
                print(f"Error fetching data for PMID {pmid}: {e}")
                return "Error"
        except Exception as e:
            print(f"Unexpected error for PMID {pmid}: {e}")
            return "Error"


def article_type_main(input_csv, output_csv):
    """
    Main function to fetch article types for PMIDs in an input CSV file.
    :param input_csv: Path to the input CSV file containing a 'pmid' column
    :param output_csv: Path to the output CSV file to save results
    """
    # Read PMIDs from the input CSV file
    data = pd.read_csv(input_csv)
    if 'pmid' not in data.columns:
        print("Error: The input CSV file does not contain a 'pmid' column.")
        return

    pmids = data['pmid'].dropna().astype(str).tolist()

    # Fetch article types
    results = []
    for pmid in pmids:
        article_types = fetch_article_type(pmid)
        results.append({"pmid": pmid, "article_type": "; ".join(article_types.replace("; ", "").split(";;"))})
        print(f"PMID {pmid}: {article_types}")

    # Save results to the output CSV file
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)

    print(f"Results saved to {output_csv}")


def generate_prompt(paper, cytokine):
    prompt = f"""
    Paper: {paper}
    Cytokines: {', '.join(cytokine)}

    Please read the Paper above and based on that paper only.

    Step 1: Check if 'cytokines' are discussed in the paper. Note that some abbreviations or terms may look similar to 'cytokines' but are not actually cytokines. Cytokines are small proteins that serve as chemical messengers in the immune system, regulating the growth and activity of other cells.


    Step 2: limit the analysis to non-cancer diseases. For each combination of cytokines and sites, answer the following questions related to the cytokine:
    - Cytokine Name: The cytokine's name (consider variations such as alpha for "a", beta for "b", receptor "R", etc. consider alternative names such as CXCL8 for IL-8, MCP-1 for CCL2). If there is no 'cytokines' discussed in Step 1, then return the name as 'None'.
    - Disease Type: The disease type mentioned.
    - Host: Indicate whether the effects are in human, other animals, or cell lines.
    - Site: Measurement site (serum or cerebrospinal fluid (CSF)). If not mentioned, return "None".
    - Association with LRRK2 mutation: 1 if the concentration of the cytokine is higher in hosts with LRRK2 mutation than without LRRK2 mutation, -1 for the reverse, 0 otherwise.
    - LRRK2 variant: the LRRK2 mutation variant. If not mentioned, return "None".
    - LRRK2 mutation type: the type of mutation such as gain of function, loss of function, etc. If not mentioned, return "None".
    - Association with LRRK2 mutation statistical significance: the test statistic such as t score, w score, and significance such as p value. Return the value as [test statistic, significance]. If not mentioned, return "None".
    - LRRK2 support: 1 to 3 sentences extracted from the paper explaining the association with LRRK2 mutation. No paraphrase is needed.
    - Association with parkinson disease: 1 if the concentration of the cytokine is higher in hosts with parkinson disease than without parkinson disease, -1 for the reverse, 0 otherwise.
    - Association with parkinson disease statistical significance: the test statistic such as t score, w score, and significance such as p value. Return the value as [test statistic, significance]. If not mentioned, return "None".
    - parkinson disease support: 1 to 3 sentences extracted from the paper explaining the association with parkinson disease.No paraphrase is needed.

    Step 3: check on the previous results based on the paper again.
    - double check if the extracted cytokine_name is the cytokine or its alternative name passed to prompt
    - Review the outputs from Step 2 against the criteria provided in the system content, focusing on key aspects such as the main topic and definition. Make any necessary corrections.
    - Ensure that the extracted texts from Step 2 are present in the paragraphs identified in Step 2. Make corrections if discrepancies are found.
    - Review the answer from Step 2 and the corresponding mechanism extracted. Make corrections if discrepancies are found. 
    """
    return prompt


def system_prompt():
    prompt = f"""
    You are an biologist assistant that specializes in extracting cytokine-related information from scientific papers.
    Update memory with the following information:
    1. Analyze association of cytokine concentration in serum or cerebrospinal fluid (CSF) with the presence of LRRK2 mutation and/or parkinson's disease.
    Take note of these criteria:
    Limit the analysis to non-cancer diseases. Exclude any cancer-related information.
    If association between cytokine concentration and multiple gene mutations is mentioned, limit the analysis to LRRK2 mutation.
    If the cytokine has different effects in preclinical (cell line, mouse model, etc.) and clinical experiments, prioritize its clinical effects.

    2. definitions of LRRK2 mutation and parkinson's disease:
	LRR2 mutation: Mutations in the leucine-rich repeat kinase 2 (LRRK2) gene are the most common genetic cause of Parkinson's disease (PD). These mutations can cause changes to the structure and function of the dardarin protein, which is encoded by the LRRK2 gene, LRRK2 mutations are noted as variants, such as dLRRK, dY1383C, dI1915T, hLRRK2, etc. The types of mutation or genetic manipulation can be loss of function, gain of function, overexpression (O/E), or other types of mutations. 

	3. definitions of positive and negative associations:
	Positive association: The concentration of the cytokine is higher in hosts with LRRK2 mutation or parkinson's disease than in hosts without the mutation or disease.If the odds ratio (OR) between PD and non PD/healthy control is provided and is greater than 1, it indicates a positive association. If the confidence interval (CI) of OR is provided and the lower bound is greater than 1, it indicates a positive association.
	Negative association: The concentration of the cytokine is lower in hosts with LRRK2 mutation or parkinson's disease than in hosts without the mutation or disease. If the OR is provided and is less than 1, it indicates a negative association. If the CI of OR is provided and the upper bound is less than 1, it indicates a negative association.
	If inhibitor/downregulation of the cytokine reduces risks of PD, the cytokine is negatively associated with PD. If the inhibitor/downregulation of the cytokine increases risks of PD, the cytokine is positively associated with PD.

	4. Alternative names of cytokines:
	Consider alternative names of cytokines, such as below examples (in the format of cytokine: alternative name) but not limited to:
	G-CSF: CSF-3
    IL-8: CXCL8
    IL-17A: CTLA-8
    BLC: CXCL13
    ENA-78: CXCL5
    Eotaxin: CCL11
    Eotaxin-2: CCL24
    Eotaxin-3: CCL26
    Fractalkine: CX3CL1
    Gro-alpha: CXCL1
    Gro-alpha: KC
    IP-10: CXCL10
    I-TAC: CXCL11
    MCP-1: CCL2
    MCP-2: CCL8
    MCP-3: CCL7
    MDC: CCL22
    MIG: CXCL9
    MIP-1 alpha: CCL3
    MIP-1 beta: CCL4
    MIP-3 alpha: CCL20
    SDF-1 alpha: CXCL12
    CD30: CD30
    CD40L: CD154
    IL-2R: CD25
    TRAIL: CD253
	Instructions:

    - For the given combination, extract the required information.
    - Explanations must be directly based on the content of the paper.Use exact sentences from the paper for the mechanisms.
    - Do not include any information not present in the paper.
    - Avoid adding any assumptions or external knowledge.
    """
    return prompt


def get_response(paper, cytokine):
    prompt = generate_prompt(paper, cytokine)
    sys_prompt = system_prompt()
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system",
             "content": sys_prompt},
            {"role": "user",
             "content": prompt}
        ],
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "LRRK2_Parkinson_Output",
                "schema": {
                    "type": "object",
                    "properties": {
                        "cytokine_name": {
                            "type": "string",
                            "description": "The name of the cytokine, with possible variations in notation such as '-', alpha (a), beta (b), etc. or None"
                        },
                        "disease_type": {
                            "type": "string",
                            "description": "The type of non-cancer disease in which the cytokine's effects are mentioned in the paper."
                        },
                        "host": {
                            "type": "string",
                            "enum": ["human", "animal", "cell line", "other"],
                            "description": "The host in which the cytokine's effects are studied (human, animal, cell line, or other)."
                        },
                        "site": {
                            "type": "string",
                            "description": "Location of cytokine measurement (serum or cerebrospinal fluid (CSF)) or 'None' if not mentioned."
                        },
                        "LRRK2_association": {
                            "type": "integer",
                            "enum": [0, 1, -1],
                            "description": "1 if the concentration of the cytokine is higher in hosts with LRRK2 mutation than without LRRK2 mutation, -1 for the reverse, 0 otherwise."
                        },
                        "LRRK2_variant": {
                            "type": "string",
                            "description": "the LRRK2 mutation variantor or 'None' if not mentioned."
                        },
                        "LRRK2_mutation_type": {
                            "type": "string",
                            "description": "the type of mutation such as gain of function, loss of function, etc, or 'None' if not mentioned."
                        },
                        "LRRK2_stats_sig": {
                            "type": "string",
                            "description": "the test statistic such as t score, w score, and significance such as p value. Return the value as [test statistic, significance]. If not mentioned, return 'None'."
                        },
                        "LRRK2_support": {
                            "type": "string",
                            "description": "A sentence extracted from the paper explaining the association with LRRK2 mutation."
                        },
                        "parkinson_association": {
                            "type": "integer",
                            "enum": [0, 1, -1],
                            "description": "1 if the concentration of the cytokine is higher in hosts with parkinson disease than without parkinson disease, -1 for the reverse, 0 otherwise."
                        },
                        "parkinson_stats_sig": {
                            "type": "string",
                            "description": "the test statistic such as t score, w score, and significance such as p value. Return the value as [test statistic, significance]. If not mentioned, return 'None'."
                        },
                        "parkinson_support": {
                            "type": "string",
                            "description": "A sentence extracted from the paper explaining the association with parkinson disease."
                        }
                    },
                    "required": [
                        "cytokine_name",
                        "disease_type",
                        "host",
                        "site",
                        "LRRK2_association",
                        "LRRK2_variant",
                        "LRRK2_mutation_type",
                        "LRRK2_stats_sig",
                        "LRRK2_support",
                        "parkinson_association",
                        "parkinson_stats_sig",
                        "parkinson_support"
                    ],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    )

    return response.choices[0].message.content


def query_cytokine(cytokine, write_dir=write_dir):
    query = f'{cytokine} AND (("LRRK2" AND parkinson) OR ("LRRK2") OR ("parkinson"))'
    print(cytokine)
    # pmids = search_pubmed(query)
    raw_output = []

    results = fetch_full_texts(query, num_articles=50)
    for pmid, year, full_text in results:
        response = get_response(full_text, cytokine)
        raw_output.append([cytokine, pmid, year, response])
    pd.DataFrame(raw_output, columns=["cytokine", "pmid", "year", "response"]).to_csv(
        f"{write_dir}{cytokine}_raw_output.txt", index=False, sep="\t")
    return raw_output


def clean_json_string(s):
    # Remove any leading/trailing whitespace and quotes
    s = s.strip().strip('"')

    # Check if the string starts with 'response' and remove it if present
    if s.startswith('response'):
        s = s[8:].strip()  # 8 is the length of 'response'

    # Replace double-escaped quotes with single quotes
    s = s.replace('""', '"')

    # If the string is enclosed in quotes, remove them
    if s.startswith('{') and s.endswith('}'):
        s = s[1:-1]

    return s


def process_cytokine_data(input_folder, output_file):
    header = ['cytokine', 'pmid', 'year', 'cytokine_name', 'disease_type', 'host', 'site',
              'LRRK2_association', 'LRRK2_variant', 'LRRK2_mutation_type',
              'LRRK2_stats_sig', 'LRRK2_support', 'parkinson_association',
              'parkinson_stats_sig', 'parkinson_support']

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header, delimiter=',')
        writer.writeheader()

        for filename in os.listdir(input_folder):
            if filename.endswith('.txt'):
                file_path = os.path.join(input_folder, filename)
                print(f"Processing file: {filename}")

                with open(file_path, 'r', encoding='utf-8') as infile:
                    for line_number, line in enumerate(infile, 1):
                        parts = re.split(r'\t(?=(?:[^"]*"[^"]*")*[^"]*$)', line.strip())
                        if len(parts) != 4:
                            print(f"Skipping invalid line {line_number} in {filename}: {line.strip()}")
                            continue

                        cytokine, pmid, year, response = parts

                        cleaned_response = clean_json_string(response)

                        try:
                            response_data = json.loads('{' + cleaned_response + '}')
                        except json.JSONDecodeError as e:
                            print(f"Error parsing JSON in {filename}, line {line_number}: {e}")
                            print(f"Problematic JSON: {cleaned_response}")
                            continue
                        if response_data:
                            row_data = {
                                'cytokine': cytokine,
                                'pmid': pmid,
                                'year': year,
                                **response_data
                            }

                            writer.writerow(row_data)

    print(f"Data processing complete. Output saved to {output_file}")


