"""
Test data generation for text similarity benchmarks.

Generates realistic Chinese-English mixed text data at various lengths
for performance testing.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import NamedTuple


class TextSample(NamedTuple):
    """A text sample with metadata."""
    text: str
    category: str
    length_category: str  # short, medium, long
    char_count: int


# Real-world text samples for generating test data
ENGLISH_NEWS_SAMPLES = [
    "The stock market experienced significant volatility today as investors reacted to the latest economic data. Technology stocks led the decline, with major companies reporting lower than expected earnings.",
    "Scientists have discovered a new species of deep-sea fish in the Pacific Ocean. The finding could help researchers understand how marine life adapts to extreme conditions.",
    "The city council approved a new infrastructure plan that will improve public transportation and reduce traffic congestion. The project is expected to create thousands of jobs.",
    "Climate researchers warn that global temperatures could rise by 2 degrees Celsius by 2050 if current emission trends continue. Governments are urged to take immediate action.",
    "The tech industry is embracing artificial intelligence at an unprecedented rate. Companies are investing billions in machine learning research and development.",
]

CHINESE_NEWS_SAMPLES = [
    "今日股市出现大幅波动，科技股领跌。分析师认为，这主要是由于最新经济数据的影响。投资者对未来市场走势持谨慎态度。",
    "中国科学家在量子计算领域取得重大突破，成功实现了多量子比特的纠错操作。这一成果将推动量子计算机的实用化进程。",
    "新能源汽车市场持续增长，多家车企宣布推出新款电动车型。专家预测，到2030年，电动汽车将占据市场主导地位。",
    "人工智能技术正在改变传统产业格局。从制造业到服务业，智能化转型已成为企业发展的必然趋势。",
    "城市规划部门发布新方案，计划在未来五年内建设更多绿色公共空间，提升居民生活质量。",
]

TECH_DOC_SAMPLES = [
    "The function accepts a dictionary of parameters and returns a processed result. Error handling is implemented using try-except blocks to ensure graceful degradation.",
    "This API endpoint supports both GET and POST requests. Authentication is required using Bearer tokens in the Authorization header.",
    "The database schema includes three main tables: users, products, and orders. Foreign key constraints ensure referential integrity.",
    "Memory management is handled automatically by the garbage collector. However, for large objects, manual cleanup may improve performance.",
    "该模块提供了高性能的文本处理功能，支持多种编码格式。使用缓存机制可以显著提升重复查询的效率。",
    "接口支持异步调用模式，可以通过回调函数或Promise处理响应。建议在高并发场景下使用连接池。",
]

SOCIAL_MEDIA_SAMPLES = [
    "Just finished an amazing workout! Feeling great and ready to take on the day. #fitness #motivation",
    "The new iPhone is absolutely stunning. The camera quality is incredible! 📱✨",
    "今天的早餐太好吃了！推荐这家店的咖啡☕️和牛角包🥐",
    "终于完成了这个项目，感谢团队的支持！🎉 期待下一个挑战！",
    "Weekend vibes 🌴 Finally got some time to relax and read a good book.",
    "新买的机械键盘到了，打字体验太棒了！程序员必备神器💻",
]


def generate_text(target_length: int, mixed: bool = True) -> str:
    """
    Generate text of approximately the target length.

    Args:
        target_length: Target character count
        mixed: Whether to mix Chinese and English

    Returns:
        Generated text
    """
    result_parts = []
    current_length = 0

    all_samples = []
    if mixed:
        all_samples = (
            ENGLISH_NEWS_SAMPLES +
            CHINESE_NEWS_SAMPLES +
            TECH_DOC_SAMPLES +
            SOCIAL_MEDIA_SAMPLES
        )
    else:
        # Alternate between all-English and all-Chinese
        if random.random() < 0.5:
            all_samples = ENGLISH_NEWS_SAMPLES + TECH_DOC_SAMPLES[:4]
        else:
            all_samples = CHINESE_NEWS_SAMPLES + [TECH_DOC_SAMPLES[4], TECH_DOC_SAMPLES[5]]

    while current_length < target_length:
        sample = random.choice(all_samples)
        result_parts.append(sample)
        current_length += len(sample)

    result = " ".join(result_parts)

    # Trim to approximate target length
    if len(result) > target_length * 1.2:
        result = result[:int(target_length * 1.1)]
        # Try to end at a sentence boundary
        for sep in ['. ', '。', '! ', '！', '? ', '？']:
            last_sep = result.rfind(sep)
            if last_sep > target_length * 0.8:
                result = result[:last_sep + len(sep)]
                break

    return result.strip()


def generate_test_dataset(
    num_samples: int = 50,
    output_path: Path | None = None
) -> dict:
    """
    Generate a complete test dataset with various text lengths.

    Args:
        num_samples: Number of samples per length category
        output_path: Optional path to save the dataset

    Returns:
        Dictionary containing the test dataset
    """
    dataset = {
        "metadata": {
            "description": "Text similarity benchmark dataset",
            "categories": ["news", "tech_doc", "social_media"],
            "length_categories": {
                "short": "~100 characters",
                "medium": "~1000 characters",
                "long": "~10000 characters"
            }
        },
        "samples": {
            "short": [],
            "medium": [],
            "long": []
        },
        "pairs": {
            "short": [],
            "medium": [],
            "long": []
        }
    }

    length_targets = {
        "short": 100,
        "medium": 1000,
        "long": 10000
    }

    for length_cat, target_len in length_targets.items():
        print(f"Generating {num_samples} {length_cat} samples (~{target_len} chars)...")

        for i in range(num_samples):
            text = generate_text(target_len, mixed=True)
            dataset["samples"][length_cat].append({
                "id": f"{length_cat}_{i}",
                "text": text,
                "char_count": len(text)
            })

        # Generate pairs for similarity testing
        print(f"Generating {num_samples} {length_cat} text pairs...")
        for i in range(num_samples):
            text1 = generate_text(target_len, mixed=True)
            text2 = generate_text(target_len, mixed=True)
            dataset["pairs"][length_cat].append({
                "id": f"pair_{length_cat}_{i}",
                "text1": text1,
                "text2": text2,
                "text1_len": len(text1),
                "text2_len": len(text2)
            })

    # Generate query-documents sets for batch testing
    print("Generating query-document sets for batch testing...")
    dataset["batch_test"] = {}

    for length_cat, target_len in length_targets.items():
        query = generate_text(target_len // 2, mixed=True)
        documents = [generate_text(target_len, mixed=True) for _ in range(100)]
        dataset["batch_test"][length_cat] = {
            "query": query,
            "documents": documents
        }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"Dataset saved to {output_path}")

    return dataset


def load_test_dataset(path: Path) -> dict:
    """Load a previously generated test dataset."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Quick access samples for testing
QUICK_TEST_SAMPLES = {
    "short_en": "The quick brown fox jumps over the lazy dog. This is a test sentence.",
    "short_cn": "敏捷的棕色狐狸跳过懒惰的狗。这是一个测试句子。",
    "short_mixed": "The AI model 人工智能模型 achieves state-of-the-art 达到最先进的 results.",
    "medium_en": " ".join(ENGLISH_NEWS_SAMPLES),
    "medium_cn": " ".join(CHINESE_NEWS_SAMPLES),
    "medium_mixed": " ".join(ENGLISH_NEWS_SAMPLES[:2] + CHINESE_NEWS_SAMPLES[:2]),
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate test data for benchmarks")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "results" / "test_data.json",
        help="Output path for the dataset"
    )
    parser.add_argument(
        "--samples", "-n",
        type=int,
        default=50,
        help="Number of samples per category"
    )

    args = parser.parse_args()

    dataset = generate_test_dataset(
        num_samples=args.samples,
        output_path=args.output
    )

    print(f"\nDataset statistics:")
    for cat in ["short", "medium", "long"]:
        samples = dataset["samples"][cat]
        avg_len = sum(s["char_count"] for s in samples) / len(samples)
        print(f"  {cat}: {len(samples)} samples, avg length: {avg_len:.0f} chars")
