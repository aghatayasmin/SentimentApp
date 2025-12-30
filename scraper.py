import requests
import pandas as pd
import time

def scrape_with_graphql():
    # 1. The API Endpoint you found
    url = "https://web-scraping.dev/api/graphql"
    
    # 2. The headers to look like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 3. The Query you found (Copy-pasted exactly)
    query = """
    query GetReviews($first: Int, $after: String) {
      reviews(first: $first, after: $after) {
        edges {
          node {
            rid
            text
            rating
            date
          }
          cursor
        }
        pageInfo {
          startCursor
          endCursor
          hasPreviousPage
          hasNextPage
        }
      }
    }
    """

    all_reviews = []
    # We start with an empty cursor (beginning of the list)
    variables = {"first": 20, "after": ""}
    
    print("Starting GraphQL Scraping...")

    while True:
        # 4. Prepare the package to send
        payload = {
            "query": query,
            "variables": variables
        }
        
        # 5. Send the POST request (Note: APIs use POST, not GET)
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break
            
        data = response.json()
        
        # 6. Dig into the JSON to find the list of reviews
        # Structure: data -> reviews -> edges -> node
        try:
            edges = data['data']['reviews']['edges']
        except TypeError:
            print("No data found or end of stream.")
            break

        # Extract data from each review
        for edge in edges:
            node = edge['node']
            review_item = {
                # We use 'rid' as the ID/Title since the API didn't give a product name
                "id": node['rid'], 
                "text": node['text'],
                "rating": node['rating'],
                "date": node['date']
            }
            all_reviews.append(review_item)

        # 7. Pagination Logic (The "Next Page" check)
        page_info = data['data']['reviews']['pageInfo']
        has_next = page_info['hasNextPage']
        end_cursor = page_info['endCursor']

        print(f"Scraped {len(edges)} reviews. Moving to next page...")

        if has_next:
            # Update the 'after' variable to point to the next page
            variables["after"] = end_cursor
            time.sleep(1) # Wait 1 second to be polite
        else:
            print("No more pages. Scraping complete!")
            break

    return all_reviews

if __name__ == "__main__":
    # Run the scraper
    data = scrape_with_graphql()
    
    # Save to CSV
    df = pd.DataFrame(data)
    
    # Optional: basic cleaning of the date column now
    # This creates a real datetime object for Python to understand later
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\nTotal Reviews Collected: {len(df)}")
    print(df.head())
    
    df.to_csv("reviews.csv", index=False)
    print("Saved to reviews.csv")