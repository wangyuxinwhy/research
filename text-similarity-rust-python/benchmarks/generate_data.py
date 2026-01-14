"""
Generate test data for benchmarking text similarity algorithms.
Creates datasets with varying text lengths and content types.
"""

import json
import random
from typing import List, Dict


def generate_english_text(length: int) -> str:
    """Generate pseudo-English text of specified length."""
    words = [
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
        "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
        "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
        "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
        "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
        "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
        "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
        "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
        "data", "analysis", "system", "information", "computer", "science", "research", "technology",
        "development", "software", "algorithm", "performance", "optimization", "benchmark", "test",
        "machine", "learning", "artificial", "intelligence", "neural", "network", "model", "training"
    ]

    result = []
    current_length = 0

    while current_length < length:
        word = random.choice(words)
        if result:
            result.append(" ")
            current_length += 1
        result.append(word)
        current_length += len(word)

    text = "".join(result)
    return text[:length]


def generate_chinese_text(length: int) -> str:
    """Generate pseudo-Chinese text of specified length."""
    chars = [
        "的", "一", "是", "在", "不", "了", "有", "和", "人", "这",
        "中", "大", "为", "上", "个", "国", "我", "以", "要", "他",
        "时", "来", "用", "们", "生", "到", "作", "地", "于", "出",
        "就", "分", "对", "成", "会", "可", "主", "发", "年", "动",
        "同", "工", "也", "能", "下", "过", "子", "说", "产", "种",
        "面", "而", "方", "后", "多", "定", "行", "学", "法", "所",
        "民", "得", "经", "十", "三", "之", "进", "着", "等", "部",
        "度", "家", "电", "力", "里", "如", "水", "化", "高", "自",
        "二", "理", "起", "小", "物", "现", "实", "加", "量", "都",
        "两", "体", "制", "机", "当", "使", "点", "从", "业", "本",
        "去", "把", "性", "好", "应", "开", "它", "合", "还", "因",
        "由", "其", "些", "然", "前", "外", "天", "政", "四", "日",
        "那", "社", "义", "事", "平", "形", "相", "全", "表", "间",
        "样", "与", "关", "各", "重", "新", "线", "内", "数", "正"
    ]

    result = []
    for _ in range(length):
        result.append(random.choice(chars))

    return "".join(result)


def generate_mixed_text(length: int) -> str:
    """Generate mixed Chinese-English text."""
    # Randomly choose whether to start with English or Chinese
    segments = []
    remaining = length

    while remaining > 0:
        segment_length = min(random.randint(10, 50), remaining)

        if random.random() < 0.5:
            segments.append(generate_english_text(segment_length))
        else:
            segments.append(generate_chinese_text(segment_length))

        remaining -= segment_length

    return "".join(segments)[:length]


def generate_similar_text(base_text: str, similarity: float) -> str:
    """
    Generate text similar to base_text with controlled similarity level.

    Args:
        base_text: Original text
        similarity: Target similarity (0.0 to 1.0)

    Returns:
        Modified text with target similarity
    """
    chars = list(base_text)
    num_changes = int(len(chars) * (1 - similarity))

    for _ in range(num_changes):
        if not chars:
            break

        operation = random.choice(['insert', 'delete', 'substitute'])

        if operation == 'insert' and len(chars) > 0:
            pos = random.randint(0, len(chars))
            chars.insert(pos, random.choice('abcdefghijklmnopqrstuvwxyz '))

        elif operation == 'delete' and len(chars) > 0:
            pos = random.randint(0, len(chars) - 1)
            chars.pop(pos)

        elif operation == 'substitute' and len(chars) > 0:
            pos = random.randint(0, len(chars) - 1)
            chars[pos] = random.choice('abcdefghijklmnopqrstuvwxyz ')

    return "".join(chars)


def generate_test_dataset() -> Dict:
    """Generate comprehensive test dataset for benchmarking."""

    dataset = {
        "short_texts": [],
        "medium_texts": [],
        "long_texts": [],
        "text_pairs": [],
        "corpus_for_bm25": []
    }

    # Generate texts of different lengths
    print("Generating short texts (100 chars)...")
    for i in range(50):
        text_type = i % 3
        if text_type == 0:
            text = generate_english_text(100)
        elif text_type == 1:
            text = generate_chinese_text(100)
        else:
            text = generate_mixed_text(100)
        dataset["short_texts"].append(text)

    print("Generating medium texts (1000 chars)...")
    for i in range(50):
        text_type = i % 3
        if text_type == 0:
            text = generate_english_text(1000)
        elif text_type == 1:
            text = generate_chinese_text(1000)
        else:
            text = generate_mixed_text(1000)
        dataset["medium_texts"].append(text)

    print("Generating long texts (10000 chars)...")
    for i in range(20):
        text_type = i % 3
        if text_type == 0:
            text = generate_english_text(10000)
        elif text_type == 1:
            text = generate_chinese_text(10000)
        else:
            text = generate_mixed_text(10000)
        dataset["long_texts"].append(text)

    print("Generating text pairs with varying similarity...")
    for base_text in dataset["short_texts"][:10]:
        for similarity in [0.9, 0.7, 0.5, 0.3]:
            similar_text = generate_similar_text(base_text, similarity)
            dataset["text_pairs"].append({
                "text1": base_text,
                "text2": similar_text,
                "target_similarity": similarity
            })

    print("Generating corpus for BM25...")
    # Generate a corpus of documents
    for i in range(100):
        doc_length = random.choice([100, 500, 1000])
        if i % 2 == 0:
            doc = generate_english_text(doc_length)
        else:
            doc = generate_mixed_text(doc_length)
        dataset["corpus_for_bm25"].append(doc)

    return dataset


def save_dataset(dataset: Dict, filename: str):
    """Save dataset to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Dataset saved to {filename}")


def main():
    """Generate and save test dataset."""
    print("Starting dataset generation...")

    dataset = generate_test_dataset()

    # Print statistics
    print("\nDataset statistics:")
    print(f"Short texts: {len(dataset['short_texts'])}")
    print(f"Medium texts: {len(dataset['medium_texts'])}")
    print(f"Long texts: {len(dataset['long_texts'])}")
    print(f"Text pairs: {len(dataset['text_pairs'])}")
    print(f"BM25 corpus: {len(dataset['corpus_for_bm25'])}")

    # Save to file
    save_dataset(dataset, "benchmarks/test_data.json")

    print("\nDataset generation complete!")


if __name__ == "__main__":
    main()
