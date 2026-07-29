"""
One-time script: Updates image_url for all products that already existed
in the database (seeded before images were added).
Run: python patch_images.py
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, update
from app.database.session import AsyncSessionLocal
from app.models.product import Product

IMAGE_MAP = {
    "sodium-chloride-nacl-500g":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/2019_Fire_season_Sodium_Chloride_Sample.jpg/800px-2019_Fire_season_Sodium_Chloride_Sample.jpg",
    "hydrochloric-acid-37-1l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Hydrochloric_acid_05.jpg/800px-Hydrochloric_acid_05.jpg",
    "nitrile-gloves-box-of-100":
        "https://images.unsplash.com/photo-1584634731339-252c581abfc5?w=800&q=80",
    "borosilicate-beaker-set-50-1000ml":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Glass_beakers.jpg/800px-Glass_beakers.jpg",
    "ethanol-95-25l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Ethanol_Flasche.jpg/600px-Ethanol_Flasche.jpg",
    "lab-safety-goggles":
        "https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?w=800&q=80",
    "ph-meter-digital":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Seven_Easy_pH_meter.jpg/800px-Seven_Easy_pH_meter.jpg",
    "micropipette-100-1000l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Transferpette-s_variable_multichannel_brand.jpg/600px-Transferpette-s_variable_multichannel_brand.jpg",
    "disposable-petri-dishes-pack-of-20":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Petri_dish.jpg/800px-Petri_dish.jpg",
    "acetone-995-1l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Acetone-sample.jpg/600px-Acetone-sample.jpg",
}

async def patch():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product))
        products = result.scalars().all()
        updated = 0
        for p in products:
            img = IMAGE_MAP.get(p.slug)
            if img and not p.image_url:
                p.image_url = img
                updated += 1
                print(f"[OK] {p.name}")
        await db.commit()
        print(f"\n✅ Updated {updated} product image(s).")

if __name__ == "__main__":
    asyncio.run(patch())
