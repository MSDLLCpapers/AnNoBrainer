# SVG <--> structure map

library(RJSONIO)
library(jsonlite)
library(httr)

json <- fromJSON("http://api.brain-map.org/api/v2/structure_graph_download/1.json")

#d <- lapply(json$msg, function(i) list(unlist(i, recursive = TRUE)))
#d <- unlist(json$msg, recursive = F)
#d <- json$msg
#d <- rjson::fromJSON(json$content)

parse_hierarchy <- function(json_part) {
  for (children in json_part$children) {
    if (length(children) > 0) {
      json_part <- c(json_part, parse_hierarchy(children))
    } else {
      json_part <- c(json_part, children)
    }
  }
  json_part$children <- list()
  return(json_part)
}

df <- parse_hierarchy(json$msg)

df2 <- data.frame(id = unlist(df[seq(1, length(df), 11)]),
                  name = unlist(df[seq(5, length(df), 11)]),
                  acronym = unlist(df[seq(4, length(df), 11)])
)

write.csv(df2, "brainStructureMappingTable.csv", row.names = F)


df3 <- data.frame(child = unlist(df[seq(1, length(df), 11)]),
                  parent = c(NA, unlist(df[seq(10, length(df), 11)]))
                  )

write.csv(df3, "parentChildStructure.csv", row.names = F)
