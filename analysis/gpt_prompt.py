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