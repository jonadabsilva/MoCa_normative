library(shiny)
library(ggplot2)
library(dplyr)
library(readr)
library(lubridate)

# ==========================================
# Data & Helper Functions
# ==========================================

# MoCA Normative Data from Rossetti et al., 2011 (Dallas Heart Study)
# Table 2 provides stratified means and standard deviations in overlapping 10-year age bins.
moca_norms <- data.frame(
  Age_Bracket = c("<35", "30-40", "35-45", "40-50", "45-55", "50-60", "55-65", "60-70", "65-75", "70-80"),
  lt12_mean = c(22.80, 22.84, 22.11, 21.36, 20.75, 19.94, 19.60, 19.30, 18.37, 16.07),
  lt12_sd   = c(3.38,  3.18,  3.33,  3.73,  3.80,  4.34,  4.14,  3.79,  3.87,  3.17),
  eq12_mean = c(24.46, 23.99, 23.02, 22.26, 21.87, 22.25, 21.58, 20.89, 20.57, 20.35),
  eq12_sd   = c(3.49,  2.93,  3.67,  3.94,  3.95,  3.46,  3.93,  4.50,  4.79,  4.91),
  gt12_mean = c(25.93, 25.81, 25.38, 25.09, 24.70, 24.34, 24.43, 24.32, 24.00, 23.60),
  gt12_sd   = c(2.48,  2.64,  3.05,  3.16,  3.24,  3.38,  3.31,  3.04,  3.35,  3.47),
  stringsAsFactors = FALSE
)

get_moca_norm <- function(age_bracket, edu_bracket) {
  row <- moca_norms[moca_norms$Age_Bracket == age_bracket, ]
  
  if (nrow(row) == 0) return(list(mean = NA, sd = NA))
  
  if (edu_bracket == "<12") {
    return(list(mean = row$lt12_mean, sd = row$lt12_sd))
  } else if (edu_bracket == "12") {
    return(list(mean = row$eq12_mean, sd = row$eq12_sd))
  } else if (edu_bracket == ">12") {
    return(list(mean = row$gt12_mean, sd = row$gt12_sd))
  } else {
    return(list(mean = NA, sd = NA))
  }
}

interpret_percentile <- function(percentile) {
  if (is.na(percentile)) return(list(classification = NA, color = "gray"))
  
  if (percentile >= 98) {
    return(list(classification = "Exceptionally High", color = "#00008B"))
  } else if (percentile >= 90) {
    return(list(classification = "Above Average", color = "#0000FF"))
  } else if (percentile >= 75) {
    return(list(classification = "High Average", color = "#00FFFF"))
  } else if (percentile >= 25) {
    return(list(classification = "Average", color = "#00FF00"))
  } else if (percentile >= 9) {
    return(list(classification = "Low Average", color = "#FFD700"))
  } else if (percentile >= 2) {
    return(list(classification = "Below Average", color = "#FF4500"))
  } else {
    return(list(classification = "Exceptionally Low", color = "#FF0000"))
  }
}

plot_normal_distribution <- function(z_score, measure_name, percentile, classification, color) {
  x_vals <- seq(-4, 4, length.out = 100)
  df <- data.frame(x = x_vals, y = dnorm(x_vals))
  point_y <- dnorm(z_score)
  
  p <- ggplot(df, aes(x = x, y = y)) +
    geom_line() +
    geom_point(aes(x = z_score, y = point_y), color = color, size = 4) +
    geom_text(aes(x = z_score, y = point_y,
                  label = sprintf("Z = %.2f\nP = %.1f%%\n%s", z_score, percentile, classification)),
              vjust = -1, size = 4) +
    labs(title = paste("Normative Distribution for", measure_name),
         subtitle = "Rossetti et al. (2011) Table 2 Reference",
         x = "Z-score", y = "Probability Density") +
    theme_minimal() +
    scale_y_continuous(expand = expansion(mult = c(0, 0.3)))
  return(p)
}

generate_csv_template <- function() {
  template <- data.frame(
    PatientName = character(0),
    Age_Bracket = character(0),
    Education_Bracket = character(0),
    TestDate = as.Date(character(0)),
    MoCA_Raw = numeric(0)
  )
  template <- rbind(template, data.frame(
    PatientName = "Example Patient",
    Age_Bracket = "60-70",
    Education_Bracket = ">12",
    TestDate = Sys.Date(),
    MoCA_Raw = 24
  ))
  return(template)
}

# ==========================================
# UI
# ==========================================
ui <- navbarPage("MoCA Normative Calculator",
                 
  tabPanel("Individual Assessment",
           sidebarLayout(
             sidebarPanel(
               textInput("patient_name", "Patient Name or ID", value = "Example Patient"),
               selectInput("age_bracket", "Age Bracket (from Table 2)", 
                           choices = moca_norms$Age_Bracket, selected = "60-70"),
               selectInput("edu_bracket", "Education (years)", 
                           choices = c("<12", "12", ">12"), selected = ">12"),
               dateInput("test_date", "Test Date", value = Sys.Date()),
               hr(),
               h4("MoCA Score"),
               radioButtons("moca_input_method", "Input Method:",
                            choices = c("Slider", "Type"), selected = "Slider"),
               conditionalPanel(
                 condition = "input.moca_input_method == 'Slider'",
                 sliderInput("moca_raw_slider", "Total Score", min = 0, max = 30, value = 24)
               ),
               conditionalPanel(
                 condition = "input.moca_input_method == 'Type'",
                 numericInput("moca_raw_num", "Total Score", value = 24, min = 0, max = 30)
               )
             ),
             
             mainPanel(
               h3("Assessment Results"),
               uiOutput("individual_results")
             )
           )
  ),
  
  tabPanel("Batch Processing",
           sidebarLayout(
             sidebarPanel(
               h4("1. Download CSV Template"),
               helpText("Important: The Age_Bracket and Education_Bracket columns in your CSV must exactly match the strings in the dropdowns (e.g., '60-70' and '>12')."),
               downloadButton("downloadTemplate", "Download Template"),
               hr(),
               h4("2. Upload Completed CSV"),
               fileInput("csv_upload", "Choose CSV File", accept = ".csv"),
               hr(),
               h4("3. Export Results"),
               downloadButton("downloadResults", "Download Processed Data")
             ),
             mainPanel(
               h3("Batch Results"),
               tableOutput("batch_table")
             )
           )
  )
)

# ==========================================
# Server
# ==========================================
server <- function(input, output, session) {
  
  get_raw_value <- function(methodInput, sliderInput, numInput) {
    if(methodInput == "Slider") {
      return(sliderInput)
    } else {
      return(numInput)
    }
  }
  
  individual_results <- reactive({
    req(input$patient_name, input$age_bracket, input$edu_bracket, input$test_date)
    
    moca_raw <- get_raw_value(input$moca_input_method, input$moca_raw_slider, input$moca_raw_num)
    norms <- get_moca_norm(input$age_bracket, input$edu_bracket)
    
    z_score <- (moca_raw - norms$mean) / norms$sd
    percentile <- pnorm(z_score) * 100
    interp <- interpret_percentile(percentile)
    
    list(
      raw = moca_raw,
      mean = norms$mean,
      sd = norms$sd,
      z = z_score,
      percentile = percentile,
      classification = interp$classification,
      plot = plot_normal_distribution(z_score, "MoCA", percentile, interp$classification, interp$color)
    )
  })
  
  output$individual_results <- renderUI({
    res <- individual_results()
    tagList(
      h4("Montreal Cognitive Assessment"),
      verbatimTextOutput("moca_text"),
      plotOutput("moca_plot")
    )
  })
  
  output$moca_text <- renderPrint({
    res <- individual_results()
    cat("Raw Score:      ", res$raw, "\n")
    cat("Expected Mean:  ", res$mean, "\n")
    cat("Expected SD:    ", res$sd, "\n")
    cat("Z-score:        ", round(res$z, 2), "\n")
    cat("Percentile:     ", round(res$percentile, 1), "%\n")
    cat("Classification: ", res$classification, "\n")
  })
  
  output$moca_plot <- renderPlot({
    individual_results()$plot
  })
  
  # Batch Processing
  output$downloadTemplate <- downloadHandler(
    filename = function() { paste0("MoCA_Template_", Sys.Date(), ".csv") },
    content = function(file) { write_csv(generate_csv_template(), file) }
  )
  
  processed_data <- reactive({
    req(input$csv_upload)
    df <- read_csv(input$csv_upload$datapath, col_types = cols(
      PatientName = col_character(),
      Age_Bracket = col_character(),
      Education_Bracket = col_character(),
      TestDate = col_date(),
      MoCA_Raw = col_double()
    ))
    
    df <- df %>%
      rowwise() %>%
      mutate(
        Expected_Mean = ifelse(!is.na(MoCA_Raw), get_moca_norm(Age_Bracket, Education_Bracket)$mean, NA),
        Expected_SD = ifelse(!is.na(MoCA_Raw), get_moca_norm(Age_Bracket, Education_Bracket)$sd, NA),
        MoCA_Z = ifelse(!is.na(MoCA_Raw) & !is.na(Expected_Mean), (MoCA_Raw - Expected_Mean) / Expected_SD, NA),
        MoCA_Percentile = ifelse(!is.na(MoCA_Z), pnorm(MoCA_Z) * 100, NA),
        Classification = ifelse(!is.na(MoCA_Percentile), interpret_percentile(MoCA_Percentile)$classification, NA)
      ) %>%
      ungroup()
      
    return(df)
  })
  
  output$batch_table <- renderTable({
    req(processed_data())
    processed_data()
  }, striped = TRUE, hover = TRUE)
  
  output$downloadResults <- downloadHandler(
    filename = function() { paste0("MoCA_Results_", Sys.Date(), ".csv") },
    content = function(file) { write_csv(processed_data(), file) }
  )
}

shinyApp(ui, server)