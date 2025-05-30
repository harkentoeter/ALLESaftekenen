from datetime import datetime, timedelta
from pushbullet import Pushbullet
from marktplaats import SearchQuery, SortBy, SortOrder, Condition, category_from_name


query = input("Zoekterm (bijv. 'gazelle'): ")
zip_code = input("Postcode (bijv. '1016LV'): ")
distance = int(input("Maximale afstand in meters (bijv. 100000): "))
price_from = int(input("Minimale prijs (bijv. 0): "))
price_to = int(input("Maximale prijs (bijv. 100): "))
condition_input = input("Conditie (NEW, AS_GOOD_AS_NEW, USED): ").upper()
category_input = input("Categorie (bijv. 'Fietsen en Brommers'): ")


try:
    condition = Condition[condition_input]
except KeyError:
    print("Ongeldige conditie opgegeven. Geldige opties: NEW, AS_GOOD_AS_NEW, USED")
    exit(1)

try:
    category = category_from_name(category_input)
except Exception:
    print("Ongeldige categorie opgegeven.")
    exit(1)


pb = Pushbullet("")


search = SearchQuery(
    query=query,
    zip_code=zip_code,
    distance=distance,
    price_from=price_from,
    price_to=price_to,
    limit=5,
    offset=0,
    sort_by=SortBy.OPTIMIZED,
    sort_order=SortOrder.ASC,
    condition=condition,
    offered_since=datetime.now() - timedelta(days=7),
    category=category
)


listings = search.get_listings()


for listing in listings:
    title = listing.title
    description = listing.description
    price = listing.price_as_string(lang="nl")
    link = listing.link
    locatie = listing.location
    datum = listing.date.strftime("%Y-%m-%d %H:%M:%S")

    message = f"{title}\nPrijs: {price}\nPlaats: {locatie}\nDatum: {datum}\nLink: {link}"
    
    
    pb.push_note(f"Nieuwe advertentie: {query}", message)

    
    print("-----------------------------")
    print(title)
    print(description)
    print(price)
    print(listing.price_type)
    print(link)
    print(locatie)
    print(listing.seller)
    print(datum)
    print(listing.seller.get_seller())
    print(listing.first_image.medium)
    for image in listing.get_images():
        print(image)
