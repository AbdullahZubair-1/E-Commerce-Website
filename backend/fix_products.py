"""
One-time fix script:
  1. Removes duplicate products (keeps the newest/better version).
  2. Ensures every remaining product has an accurate image URL.

Run: python fix_products.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete
from app.database.session import AsyncSessionLocal
from app.models.product import Product

# ── Duplicates to remove (old slugs from first seed) ──────────────────────────
SLUGS_TO_DELETE = [
    "acetone-99-5-1l",          # replaced by "acetone-99-5-1-l"
    "ethanol-95-2-5l",          # replaced by "ethanol-95-2-5-l"
    "borosilicate-beaker-set-501000-ml",  # replaced by "borosilicate-beaker-set-50-1000ml"
    "micropipette-1001000-l",   # replaced by "micropipette-100-1000l"
    "ph-meter-digital",         # replaced by "digital-ph-meter"
    "sterile-petri-dishes-pack-of-20",  # replaced by "disposable-petri-dishes-pack-of-20"
]

# ── Complete image map for every product slug ──────────────────────────────────
IMAGE_MAP = {
    "sodium-chloride-nacl-500g":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/2019_Fire_season_Sodium_Chloride_Sample.jpg/800px-2019_Fire_season_Sodium_Chloride_Sample.jpg",

    "hydrochloric-acid-37-1l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Hydrochloric_acid_05.jpg/800px-Hydrochloric_acid_05.jpg",

    "nitrile-gloves-box-of-100":
        "https://images.unsplash.com/photo-1584634731339-252c581abfc5?w=800&q=80",

    "borosilicate-beaker-set-50-1000ml":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Glass_beakers.jpg/800px-Glass_beakers.jpg",

    "borosilicate-beaker-set-501000-ml":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Glass_beakers.jpg/800px-Glass_beakers.jpg",

    "ethanol-95-2-5-l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Ethanol_Flasche.jpg/600px-Ethanol_Flasche.jpg",

    "ethanol-95-2-5l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Ethanol_Flasche.jpg/600px-Ethanol_Flasche.jpg",

    "lab-safety-goggles":
        "https://images.unsplash.com/photo-1581594693702-fbdc51b2763b?w=800&q=80",

    "digital-ph-meter":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Seven_Easy_pH_meter.jpg/800px-Seven_Easy_pH_meter.jpg",

    "ph-meter-digital":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Seven_Easy_pH_meter.jpg/800px-Seven_Easy_pH_meter.jpg",

    "micropipette-100-1000l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Single_channel_pipette.jpg/600px-Single_channel_pipette.jpg",

    "micropipette-1001000-l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Single_channel_pipette.jpg/600px-Single_channel_pipette.jpg",

    "disposable-petri-dishes-pack-of-20":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Petri_dish.jpg/800px-Petri_dish.jpg",

    "sterile-petri-dishes-pack-of-20":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Petri_dish.jpg/800px-Petri_dish.jpg",

    "acetone-99-5-1-l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Acetone-sample.jpg/600px-Acetone-sample.jpg",

    "acetone-99-5-1l":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Acetone-sample.jpg/600px-Acetone-sample.jpg",

    "conical-flask-erlenmeyer-250-ml":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Erlenmeyer_Flask.jpg/600px-Erlenmeyer_Flask.jpg",

    "sulfuric-acid-98-500-ml":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Sulfuric_acid_2.jpg/600px-Sulfuric_acid_2.jpg",

    "lab-coat-white-size-l":
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&q=80",

    "analytical-balance-0-0001-g":
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Analytical_balance_mettler.jpg/800px-Analytical_balance_mettler.jpg",

    "disposable-syringes-10-ml-pack-of-50":
        "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&q=80",
}


async def fix():
    async with AsyncSessionLocal() as db:

        # ── Step 1: Remove duplicate old products ──────────────────────────────
        deleted = 0
        for slug in SLUGS_TO_DELETE:
            product = (await db.execute(
                select(Product).where(Product.slug == slug)
            )).scalar_one_or_none()
            if product:
                await db.delete(product)
                deleted += 1
                print(f"[DEL]  Removed duplicate: {product.name} ({slug})")

        # ── Step 2: Set image on every product ─────────────────────────────────
        all_products = (await db.execute(select(Product))).scalars().all()
        img_updated = 0
        for p in all_products:
            img = IMAGE_MAP.get(p.slug)
            if img:
                if p.image_url != img:
                    p.image_url = img
                    img_updated += 1
                    print(f"[IMG]  {p.name}")
            else:
                print(f"[WARN] No image mapped for slug: {p.slug}")

        await db.commit()
        print(f"\n✅ Done — removed {deleted} duplicate(s), updated {img_updated} image(s).")


if __name__ == "__main__":
    asyncio.run(fix())
