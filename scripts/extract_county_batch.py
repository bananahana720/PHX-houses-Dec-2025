
# Target properties with hashes
properties = [
    {
        "address": "2344 W Marconi Ave, Phoenix, AZ 85023",
        "hash": "5b8b1e28",
        "search_term": "2344 W Marconi"
    },
    {
        "address": "4732 W Davis Rd, Glendale, AZ 85306",
        "hash": "ef7cd95f",
        "search_term": "4732 W Davis"
    },
    {
        "address": "4417 W Sandra Cir, Glendale, AZ 85308",
        "hash": "3e28ac5f",
        "search_term": "4417 W Sandra"
    },
    {
        "address": "2846 W Villa Rita Dr, Phoenix, AZ 85053",
        "hash": "d07c4ec2",
        "search_term": "2846 W Villa Rita"
    },
    {
        "address": "4209 W Wahalla Ln, Glendale, AZ 85308",
        "hash": "78399f38",
        "search_term": "4209 W Wahalla"
    }
]

# Build search URLs
for prop in properties:
    search_url = f"https://mcassessor.maricopa.gov/mcs/?q={prop['search_term'].replace(' ', '%20')}"
    print(f"Property: {prop['address']}")
    print(f"Hash: {prop['hash']}")
    print(f"Search URL: {search_url}")
    print()
