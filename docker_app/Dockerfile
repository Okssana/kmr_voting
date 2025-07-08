FROM python:3.9-slim

WORKDIR /data

# Install Datasette and plugins
RUN pip install --no-cache-dir \
    datasette \
    datasette-vega \
    datasette-cluster-map \
    datasette-pretty-json \
    datasette-search-all \
    datasette-hashed-urls \  
    uvicorn[standard]  

# The actual database and metadata will be mounted as volumes
# but we create placeholder files to document what's needed
RUN touch kmr_voting_data.db metadata.json

# Create necessary directories
RUN mkdir -p static

COPY static/custom.css static/custom.css

# Expose the port
EXPOSE 8001

# Set the command to run Datasette with the right settings
CMD ["sh", "-c", "datasette inspect kmr_voting_data.db --inspect-file=counts.json && \
    datasette -i kmr_voting_data.db --metadata metadata.json \
    --host 0.0.0.0 --port 8001 \
    --inspect-file=counts.json \
    --static static:static \
    --setting sql_time_limit_ms 60000 \
    --setting facet_time_limit_ms 1000 \
    --setting facet_suggest_time_limit_ms 1000 \
    --setting default_page_size 50 \
    --setting max_returned_rows 1000 \
    --setting num_sql_threads 4 \
    --setting cache_size_kb 50000 \
    --setting truncate_cells_html 500"]


#CMD ["datasette", "-i", "--host", "0.0.0.0", "--port", "8001", "kmr_voting_data.db", "--metadata", "metadata.json", "--setting", "sql_time_limit_ms", "60000", "--setting", "max_returned_rows", "1000", "--setting", "num_sql_threads", "4", "--setting", "cache_size_kb", "50000", "--setting", "truncate_cells_html", "50"]
#CMD ["datasette", "--host", "0.0.0.0", "--port", "8001", "/data/kmr_voting_data.db", "-m", "/data/metadata.json", "--setting", "sql_time_limit_ms", "60000", "--setting", "max_returned_rows", "1000", "--setting", "num_sql_threads", "4", "--setting", "cache_size_kb", "50000", "--setting", "allow_facet", "true", "--setting", "hash_urls", "1", "--setting", "truncate_cells_html", "50"]
#CMD ["datasette", "--host", "0.0.0.0", "--port", "8001", "/data/kmr_voting_data.db", "--metadata", "/data/metadata.json", "--setting", "sql_time_limit_ms", "60000", "--setting", "max_returned_rows", "1000", "--setting", "num_sql_threads", "4", "--setting", "cache_size_kb", "50000", "--setting", "allow_facet", "true", "--setting", "hash_urls", "1", "--setting", "truncate_cells_html", "50"]