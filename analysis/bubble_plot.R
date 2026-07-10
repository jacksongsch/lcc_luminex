# install.packages("readxl")
library(readxl)
library(ggplot2)
library(dplyr)
serum_df <- read_excel('data/Luminex/data for bubble plot.xlsx', sheet = "serum")
csf_df <- read_excel('data/Luminex/data for bubble plot.xlsx', sheet = "csf")
serum_df['type'] = 'serum'
csf_df['type'] = 'csf'
df = rbind(serum_df, csf_df)
#   Analytes           Mean `Detection Percentage` type
pdf("plots/peng_lab_cytokine_bubble_plot.pdf", width=20, height = 4)
p <- ggplot(df, aes(x = Analytes, y = type, size = `Detection Percentage`, color = Mean)) +
  geom_point() +
  scale_size_continuous(range = c(1, 8)) +  # Adjust the range for dot size
  scale_color_gradient(low = "grey", high = "maroon") +  # Adjust color scale
  labs(x = "Cytokine", y = "Site", size = "Detection Percentage", color = "Mean") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        plot.margin = margin(2, 1, 1, 1, "cm"))
print(p)

p <- ggplot(df %>% filter(df$Analytes %in% unique(df %>% filter(Mean >= 1000))$Analytes), aes(x = Analytes, y = type, size = `Detection Percentage`, color = Mean)) +
  geom_point() +
  scale_size_continuous(range = c(1, 8)) +  # Adjust the range for dot size
  scale_color_gradient(low = "grey", high = "maroon") +  # Adjust color scale
  labs(x = "Cytokine", y = "Site", size = "Detection Percentage", color = "Mean") +
  ggtitle("Cytokines with Mean >= 1000") + 
  theme_minimal() +
  
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        plot.margin = margin(2, 1, 1, 1, "cm"))
print(p)

p <- ggplot(df %>% filter(!df$Analytes %in% (df %>% filter(Mean >= 1000))$Analytes), aes(x = Analytes, y = type, size = `Detection Percentage`, color = Mean)) +
  geom_point() +
  scale_size_continuous(range = c(1, 8)) +  # Adjust the range for dot size
  scale_color_gradient(low = "grey", high = "maroon") +  # Adjust color scale
  labs(x = "Cytokine", y = "Site", size = "Detection Percentage", color = "Mean") +
  ggtitle("Cytokines with Mean < 1000") + 
  theme_minimal() +
  
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        plot.margin = margin(2, 1, 1, 1, "cm"))
print(p)

dev.off()
