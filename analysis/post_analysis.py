#############################################################
# Supply your path to llm output and article type csv files #
#############################################################

import copy
import pandas as pd
import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
sns.set_theme(style='white')
import copy

llm_output = pd.read_csv("Data/LRRK2_parkinson_output_results.csv")
article_type = pd.read_csv("Data/LRRK2_parkinson_pmid_article_types_cleaned.csv")

##################
# pre-processing #
##################
# remove cytokine_name is NaN
llm_output = llm_output.dropna(subset=['cytokine_name'])
# fill na
llm_output['site'] = llm_output['site'].fillna('NA')
llm_output['disease_type'] = llm_output['disease_type'].fillna('NA')
llm_output['host'] = llm_output['host'].fillna('NA')

# recode cerebrospinal_fluid to CSF
llm_output['site'] = llm_output['site'].replace('cerebrospinal fluid','CSF')

# filter article types
exclude_keywords = ['Review', 'Editorial', 'Meta-Analysis', 'Letter', 'Comment', 'Preprint']
article_type['primary'] = ~article_type['article_type'].str.contains('|'.join(exclude_keywords), case=False, na=False)
print(sum(article_type['primary']))
article_type.head()

llm_output = llm_output.merge(article_type.drop_duplicates(), on='pmid', how='inner')
filtered_llmoutput = llm_output.loc[llm_output.primary,]

###############################
# Figure: publication by year #
###############################
count_data = llm_output.groupby(['year', 'cytokine'])['pmid'].nunique().reset_index(name='count')

# Calculate total count by cytokine and determine top 5% threshold
total_counts = count_data.groupby('cytokine')['count'].sum().sort_values(ascending=True)

ordered_cytokines = total_counts.index
pivot_data = count_data.pivot(index='year', columns='cytokine', values='count').fillna(0)
pivot_data = pivot_data[ordered_cytokines]  # Order columns in pivoted data
pivot_data.to_csv("Output/PMID_year_cytokine.csv")

fig, ax = plt.subplots(figsize=(10, 6))
pivot_data.plot(kind='bar', stacked=True, colormap='viridis_r', ax=ax)
ax.set_xlabel(None)
ax.set_ylabel('PMIDs')
plt.xticks(rotation=45, ha='right')
handles, labels = ax.get_legend_handles_labels()
plt.legend(handles=reversed(handles), labels=reversed(ordered_cytokines),
           fontsize='small', bbox_to_anchor=(1.05, 1), loc='upper left',
           borderaxespad=0., ncol=2, title=None)

plt.tight_layout()
plt.subplots_adjust(right=0.8)

# Save the plot with bbox_inches="tight" to prevent clipping
plt.savefig('LRRK2_parkinson/output_figures/PMID_year_cytokine.jpeg', dpi=600, bbox_inches="tight")
plt.show()

########################################
# Association with Parkinson's disease #
########################################
# exclude reviews
llm_output = filtered_llmoutput
pd_association = llm_output.loc[:, ['cytokine', 'pmid', 'cytokine_name', 'disease_type', 'host', 'site',
                                    'parkinson_association','parkinson_stats_sig', 'parkinson_support']].dropna(subset=['parkinson_support'])
pd_association = pd_association.loc[~pd_association.disease_type.isin(['Traumatic brain injury (TBI)', "depression in Parkinson's disease (dPD)"])]
pd_association_total = pd_association.groupby('cytokine', as_index=False).parkinson_association.mean()
pd_association_total.columns = ['cytokine', 'parkinson_association_total']
pd_association_total.sort_values('parkinson_association_total', ascending=False, inplace=True)

pmid_count = pd_association.groupby("cytokine", as_index=False).agg(pmid_count=('pmid', 'nunique'))
pmid_count.columns = ['cytokine', 'total_pmid']
pmid_count_human = pd_association.loc[pd_association.host=="human"].groupby("cytokine", as_index=False).agg(pmid_count=('pmid', 'nunique'))
pmid_count_human.columns = ['cytokine', 'total_pmid']

pa_association_count = pd_association.groupby(['cytokine', "parkinson_association"], as_index=False).nunique("pmid")[['cytokine', 'parkinson_association', 'pmid']]
pa_association_count.columns = ['cytokine', 'parkinson_association', 'pmid_count']
pa_association_count = pa_association_count.merge(pmid_count, on='cytokine')
pa_association_count['asso.perc'] = pa_association_count['pmid_count']/pa_association_count['total_pmid']

pa_association_count.to_csv("Output/association_cytokine_all_primary_only.csv", index=False)
pa_association_count['parkinson_association'] = pd.Categorical(pa_association_count['parkinson_association'], categories=[-1,0,1], ordered=True)
pa_association_count['parkinson_association'] = pa_association_count['parkinson_association'].map({-1: 'negative', 0: 'non', 1: 'positive'})
pa_association_count['pmid_count'] = pa_association_count['pmid_count'].astype(float)
pa_association_count.sort_values('cytokine', ascending=False, inplace=True)

# All hosts

plt.figure(figsize=(4.5,12))
bubble_plot = sns.scatterplot(
    data=pa_association_count,
    x='parkinson_association',
    y='cytokine',
    size='pmid_count',
    sizes=(10, 300),  # Adjust the range of bubble sizes as needed
    # hue='pmid_count', # 'parkinson_association',  # Optional: Color circles based on 'asso.perc'
    color='teal',  # Choose a color palette
    # alpha=0.7,
    edgecolor='w'
)

plt.xlim(-0.5, len(pa_association_count['parkinson_association'].unique()) - 0.5)  # Center categorical labels
plt.ylim(-0.5, len(pa_association_count['cytokine'].unique()) + 0.5)  # Add padding for bubbles

bubble_size_range = (10, 300)
legend_sizes = [5, 10, 20, 30, 40]
scale = (bubble_size_range[1] - bubble_size_range[0]) / (max(pa_association_count['pmid_count']) - min(pa_association_count['pmid_count']))
legend_bubble_sizes = [bubble_size_range[0] + (size - min(pa_association_count['pmid_count'])) * scale for size in legend_sizes]

legend_handles = [
    plt.scatter([], [], s=size, color='teal', edgecolor='w')
    for size in legend_bubble_sizes
]
plt.legend(
    legend_handles,
    [str(size) for size in legend_sizes],
    title="PMID Count",
    bbox_to_anchor=(1.05, 1),
    loc='best', frameon=False,
    labelspacing=0.8
)

plt.xlabel(None)
plt.ylabel(None)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('LRRK2_parkinson/output_figures/association_cytokine_bubble_all_primary_only.jpeg', dpi=600, bbox_inches="tight")

plt.show()

# Human only
pa_association_count_human = pd_association.loc[pd_association.host=="human"].groupby(['cytokine', "parkinson_association"], as_index=False).nunique("pmid")[['cytokine', 'parkinson_association', 'pmid']]
pa_association_count_human.columns = ['cytokine', 'parkinson_association', 'pmid_count']
pa_association_count_human = pa_association_count_human.merge(pmid_count_human, on='cytokine')
pa_association_count_human['asso.perc'] = pa_association_count_human['pmid_count']/pa_association_count_human['total_pmid']
pa_association_count_human = pa_association_count_human.merge(pd_association_total, on='cytokine')
pa_association_count_human.sort_values('parkinson_association_total', ascending=False, inplace=True)
pa_association_count_human.to_csv("Output/association_cytokine_human_primary_only.csv", index=False)

pa_association_count_human['parkinson_association'] = pd.Categorical(pa_association_count_human['parkinson_association'], categories=[-1,0,1], ordered=True)
pa_association_count_human['parkinson_association'] = pa_association_count_human['parkinson_association'].map({-1: 'negative', 0: 'non', 1: 'positive'})
pa_association_count_human.sort_values('cytokine', ascending=False, inplace=True)

plt.figure(figsize=(4,12))
bubble_plot = sns.scatterplot(
    data=pa_association_count_human,
    x='parkinson_association',
    y='cytokine',
    size='pmid_count',
    sizes=(10, 300),  # Adjust the range of bubble sizes as needed
    color='teal',
    edgecolor='w'
)

plt.xlim(-0.5, len(pa_association_count_human['parkinson_association'].unique()) - 0.5)  # Center categorical labels
plt.ylim(-0.5, len(pa_association_count_human['cytokine'].unique()))  # Add padding for bubbles

bubble_size_range = (10, 300)
legend_sizes = [5, 10, 15]
scale = (bubble_size_range[1] - bubble_size_range[0]) / (max(pa_association_count_human['pmid_count']) - min(pa_association_count_human['pmid_count']))
legend_bubble_sizes = [bubble_size_range[0] + (size - min(pa_association_count_human['pmid_count'])) * scale for size in legend_sizes]

legend_handles = [
    plt.scatter([], [], s=size, color='teal', edgecolor='w')
    for size in legend_bubble_sizes
]

plt.legend(
    legend_handles,
    [str(size) for size in legend_sizes],
    title="PMID Count",
    bbox_to_anchor=(1.05, 1),
    loc='best', frameon=False,
    labelspacing=0.8
)
plt.xlabel(None)
plt.ylabel(None)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('LRRK2_parkinson/output_figures/association_cytokine_bubble_human_primary_only.jpeg', dpi=600, bbox_inches="tight")
plt.show()


