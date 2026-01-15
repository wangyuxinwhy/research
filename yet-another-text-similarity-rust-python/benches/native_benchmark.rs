use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use text_similarity_rs::{
    cosine_similarity_native,
    levenshtein_distance_native,
    jaccard_similarity_native,
    bm25_score_native,
};

// Test data - matching the Python benchmarks
const SHORT_TEXT_1: &str = "The stock market experienced significant volatility today as investors reacted to the latest economic data. Technology stocks led the decline.";
const SHORT_TEXT_2: &str = "Scientists have discovered a new species of deep-sea fish in the Pacific Ocean. The finding could help researchers understand marine life.";

const MEDIUM_TEXT_1: &str = "The stock market experienced significant volatility today as investors reacted to the latest economic data. Technology stocks led the decline, with major companies reporting lower than expected earnings. Scientists have discovered a new species of deep-sea fish in the Pacific Ocean. The finding could help researchers understand how marine life adapts to extreme conditions. The city council approved a new infrastructure plan that will improve public transportation and reduce traffic congestion. The project is expected to create thousands of jobs. Climate researchers warn that global temperatures could rise by 2 degrees Celsius by 2050 if current emission trends continue. Governments are urged to take immediate action. The tech industry is embracing artificial intelligence at an unprecedented rate. Companies are investing billions in machine learning research and development. 今日股市出现大幅波动，科技股领跌。分析师认为，这主要是由于最新经济数据的影响。投资者对未来市场走势持谨慎态度。中国科学家在量子计算领域取得重大突破，成功实现了多量子比特的纠错操作。这一成果将推动量子计算机的实用化进程。";

const MEDIUM_TEXT_2: &str = "新能源汽车市场持续增长，多家车企宣布推出新款电动车型。专家预测，到2030年，电动汽车将占据市场主导地位。人工智能技术正在改变传统产业格局。从制造业到服务业，智能化转型已成为企业发展的必然趋势。城市规划部门发布新方案，计划在未来五年内建设更多绿色公共空间，提升居民生活质量。The function accepts a dictionary of parameters and returns a processed result. Error handling is implemented using try-except blocks to ensure graceful degradation. This API endpoint supports both GET and POST requests. Authentication is required using Bearer tokens in the Authorization header. The database schema includes three main tables: users, products, and orders. Foreign key constraints ensure referential integrity.";

fn generate_long_text() -> (String, String) {
    let base1 = MEDIUM_TEXT_1.repeat(10);
    let base2 = MEDIUM_TEXT_2.repeat(10);
    (base1, base2)
}

fn bench_cosine_similarity(c: &mut Criterion) {
    let mut group = c.benchmark_group("cosine_similarity_native");

    // Short text
    group.bench_with_input(
        BenchmarkId::new("short", "~140 chars"),
        &(SHORT_TEXT_1, SHORT_TEXT_2),
        |b, (t1, t2)| b.iter(|| cosine_similarity_native(black_box(t1), black_box(t2)))
    );

    // Medium text
    group.bench_with_input(
        BenchmarkId::new("medium", "~1200 chars"),
        &(MEDIUM_TEXT_1, MEDIUM_TEXT_2),
        |b, (t1, t2)| b.iter(|| cosine_similarity_native(black_box(t1), black_box(t2)))
    );

    // Long text
    let (long1, long2) = generate_long_text();
    group.bench_with_input(
        BenchmarkId::new("long", "~12000 chars"),
        &(long1.as_str(), long2.as_str()),
        |b, (t1, t2)| b.iter(|| cosine_similarity_native(black_box(t1), black_box(t2)))
    );

    group.finish();
}

fn bench_levenshtein_distance(c: &mut Criterion) {
    let mut group = c.benchmark_group("levenshtein_distance_native");

    // Short text
    group.bench_with_input(
        BenchmarkId::new("short", "~140 chars"),
        &(SHORT_TEXT_1, SHORT_TEXT_2),
        |b, (t1, t2)| b.iter(|| levenshtein_distance_native(black_box(t1), black_box(t2)))
    );

    // Medium text (reduce sample size for slow algorithm)
    group.sample_size(20);
    group.bench_with_input(
        BenchmarkId::new("medium", "~1200 chars"),
        &(MEDIUM_TEXT_1, MEDIUM_TEXT_2),
        |b, (t1, t2)| b.iter(|| levenshtein_distance_native(black_box(t1), black_box(t2)))
    );

    // Skip long text for Levenshtein (too slow even for native Rust)

    group.finish();
}

fn bench_jaccard_similarity(c: &mut Criterion) {
    let mut group = c.benchmark_group("jaccard_similarity_native");

    // Short text
    group.bench_with_input(
        BenchmarkId::new("short", "~140 chars"),
        &(SHORT_TEXT_1, SHORT_TEXT_2),
        |b, (t1, t2)| b.iter(|| jaccard_similarity_native(black_box(t1), black_box(t2)))
    );

    // Medium text
    group.bench_with_input(
        BenchmarkId::new("medium", "~1200 chars"),
        &(MEDIUM_TEXT_1, MEDIUM_TEXT_2),
        |b, (t1, t2)| b.iter(|| jaccard_similarity_native(black_box(t1), black_box(t2)))
    );

    // Long text
    let (long1, long2) = generate_long_text();
    group.bench_with_input(
        BenchmarkId::new("long", "~12000 chars"),
        &(long1.as_str(), long2.as_str()),
        |b, (t1, t2)| b.iter(|| jaccard_similarity_native(black_box(t1), black_box(t2)))
    );

    group.finish();
}

fn bench_bm25_score(c: &mut Criterion) {
    let mut group = c.benchmark_group("bm25_score_native");

    // Short text
    group.bench_with_input(
        BenchmarkId::new("short", "~140 chars"),
        &(SHORT_TEXT_1, SHORT_TEXT_2),
        |b, (query, doc)| b.iter(|| bm25_score_native(black_box(query), black_box(doc), 1.5, 0.75, None))
    );

    // Medium text
    group.bench_with_input(
        BenchmarkId::new("medium", "~1200 chars"),
        &(MEDIUM_TEXT_1, MEDIUM_TEXT_2),
        |b, (query, doc)| b.iter(|| bm25_score_native(black_box(query), black_box(doc), 1.5, 0.75, None))
    );

    // Long text
    let (long1, long2) = generate_long_text();
    group.bench_with_input(
        BenchmarkId::new("long", "~12000 chars"),
        &(long1.as_str(), long2.as_str()),
        |b, (query, doc)| b.iter(|| bm25_score_native(black_box(query), black_box(doc), 1.5, 0.75, None))
    );

    group.finish();
}

criterion_group!(
    benches,
    bench_cosine_similarity,
    bench_levenshtein_distance,
    bench_jaccard_similarity,
    bench_bm25_score
);

criterion_main!(benches);
