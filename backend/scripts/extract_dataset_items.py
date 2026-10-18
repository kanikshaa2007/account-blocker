import pandas as pd

df = pd.read_csv(r"C:\Users\kanik\Downloads\fake-real data\master_fake_real_clean.csv", low_memory=False)
df = df[df["label_binary"].notna()]

fake_items = df[(df["label_binary"] == 1.0) & (df["source_dataset"] == "LIAR")].head(3)
real_items = df[(df["label_binary"] == 0.0) & (df["source_dataset"] == "LIAR")].head(2)
myth = df[df["source_dataset"] == "India_MythFacts"].head(2)

print("=== FAKE ===")
for _, r in fake_items.iterrows():
    print("TITLE:", r["title"][:100])
    print("LABEL:", r["label_text"], "| SPEAKER:", r["speaker"])
    print()

print("=== REAL ===")
for _, r in real_items.iterrows():
    print("TITLE:", r["title"][:100])
    print("LABEL:", r["label_text"], "| SPEAKER:", r["speaker"])
    print()

print("=== INDIA MYTH FACTS ===")
for _, r in myth.iterrows():
    print("TITLE:", r["title"][:100])
    print("LABEL:", r["label_text"], "| SPEAKER:", r["speaker"])
    print()
