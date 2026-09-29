"""Konstanta, rubrik, dan profil mode untuk Argument Battle Royale.

Semua angka yang memengaruhi hasil turnamen didefinisikan di sini agar
transparan dan dapat diaudit. Laporan akhir mencetak ulang nilai-nilai ini.
"""

SCHEMA_VERSION = 1
ENGINE_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Rubrik pengujian (filsafat analitik + filsafat sains). Bobot total = 100.
# Skor per kriteria 0-10; total tertimbang = sum(skor * bobot) / 10 -> 0..100.
# ---------------------------------------------------------------------------
RUBRIC = [
    {
        "key": "clarity",
        "weight": 10,
        "label": {"id": "Kejelasan konseptual", "en": "Conceptual clarity"},
    },
    {
        "key": "validity",
        "weight": 15,
        "label": {"id": "Validitas / kekuatan inferensial", "en": "Validity / inferential strength"},
    },
    {
        "key": "premise_plausibility",
        "weight": 15,
        "label": {"id": "Plausibilitas premis", "en": "Premise plausibility"},
    },
    {
        "key": "empirical_adequacy",
        "weight": 10,
        "label": {"id": "Kecukupan empiris", "en": "Empirical adequacy"},
    },
    {
        "key": "falsifiability",
        "weight": 10,
        "label": {"id": "Keterujian / falsifiabilitas", "en": "Testability / falsifiability"},
    },
    {
        "key": "counterexample_robustness",
        "weight": 10,
        "label": {"id": "Ketahanan terhadap kontra-contoh", "en": "Robustness to counterexamples"},
    },
    {
        "key": "explanatory_power",
        "weight": 10,
        "label": {"id": "Daya eksplanatoris", "en": "Explanatory power"},
    },
    {
        "key": "parsimony",
        "weight": 5,
        "label": {"id": "Parsimoni", "en": "Parsimony"},
    },
    {
        "key": "coherence",
        "weight": 5,
        "label": {"id": "Koherensi dengan pengetahuan latar", "en": "Coherence with background knowledge"},
    },
    {
        "key": "dialectical_charity",
        "weight": 10,
        "label": {"id": "Kejujuran dialektis", "en": "Dialectical fairness"},
    },
]
RUBRIC_KEYS = [c["key"] for c in RUBRIC]
RUBRIC_WEIGHTS = [c["weight"] for c in RUBRIC]
assert sum(RUBRIC_WEIGHTS) == 100

# Selisih total (skala 0-100) di bawah ambang ini dianggap "seri praktis";
# pada seri praktis, pilihan holistik juri yang menentukan.
NEAR_TIE = 1.0

# Cacat fatal: argumen dengan lebih sedikit cacat fatal menang lebih dulu.
FATAL_FLAWS = {
    "FF_CIRCULAR": "Sirkular / petitio principii: kesimpulan diasumsikan dalam premis.",
    "FF_CONTRADICTION": "Kontradiksi internal antar-premis atau premis-kesimpulan.",
    "FF_EQUIVOCATION": "Ekuivokasi: istilah kunci berganti makna di tengah argumen.",
    "FF_NON_SEQUITUR": "Non sequitur pada inferensi sentral.",
    "FF_STRAWMAN": "Manusia jerami: posisi lawan yang menjadi tumpuan disalahrepresentasikan.",
    "FF_AD_HOC": "Imunisasi ad hoc: posisi dibuat kebal dari setiap bukti tandingan.",
    "FF_FALSE_CORE_FACT": "Klaim faktual inti yang jelas keliru menurut pengetahuan mapan.",
    "FF_PERSUASIVE_DEFINITION": "Definisi persuasif yang memenangkan perdebatan secara verbal.",
}

# Kode diskualifikasi pada tahap VALIDASI.
DQ_CODES = {
    "DQ_NOT_ARGUMENT": "Tidak memiliki struktur inferensial (hanya pernyataan/opini).",
    "DQ_OFF_TOPIC": "Tidak menjawab pertanyaan/topik yang dipertarungkan.",
    "DQ_NO_POSITION": "Kesimpulan tidak mengambil posisi apa pun terhadap topik.",
    "DQ_CONTRADICTION": "Kontradiksi internal yang tidak dapat diperbaiki.",
    "DQ_CIRCULAR": "Sirkular secara terang-terangan.",
    "DQ_UNINTELLIGIBLE": "Tidak dapat dipahami / tidak koheren secara linguistik.",
    "DQ_FALSE_CORE_FACT": "Bertumpu pada fakta inti yang jelas keliru.",
    "DQ_STANCE_MISMATCH": "Kesimpulan bertentangan dengan posisi yang ditugaskan (salah label).",
}

# Kode pengganti yang dipakai engine (bukan juri).
ENGINE_DQ_CODES = {
    "DQ_UNSCORED": "Paket scouting gagal berulang kali; petarung tidak dapat dinilai.",
}

# Lensa juri panel. Semua lensa memakai rubrik yang SAMA; lensa hanya
# menentukan apa yang diperiksa paling keras.
LENSES = [
    {
        "id": "L1",
        "label": "Logikawan formal",
        "focus": "Rekonstruksi bentuk logis, validitas/kekuatan inferensi, sesat pikir formal dan informal, ekuivokasi.",
    },
    {
        "id": "L2",
        "label": "Filsuf sains",
        "focus": "Kecukupan empiris, falsifiabilitas (Popper), inferensi ke penjelasan terbaik, parsimoni, program riset (Lakatos): inti keras vs sabuk pelindung.",
    },
    {
        "id": "L3",
        "label": "Analis konseptual",
        "focus": "Kejernihan definisi, analisis kondisi perlu/cukup, eksperimen pikiran, kontra-contoh, kasus batas.",
    },
    {
        "id": "L4",
        "label": "Skeptis / advokat setan",
        "focus": "Serangan terkuat terhadap setiap argumen, alokasi beban pembuktian, asumsi tersembunyi.",
    },
    {
        "id": "L5",
        "label": "Metodolog bukti",
        "focus": "Kualitas bukti, base rate, bias seleksi, generalisasi berlebihan, klaim empiris yang tidak didukung.",
    },
    {
        "id": "L6",
        "label": "Hakim dialektis-integratif",
        "focus": "Kejujuran dialektis, steelman lawan, konsiliensi lintas bidang, kesesuaian cakupan klaim dengan dukungannya.",
    },
    {
        "id": "L7",
        "label": "Generalis mata-segar",
        "focus": "Penilaian menyeluruh tanpa lensa khusus; periksa apakah argumen sungguh menjawab pertanyaan.",
    },
]
LENS_BY_ID = {lens["id"]: lens for lens in LENSES}
SINGLE_JUDGE_LENS = "L7"

INFERENCE_TYPES = [
    "deductive",
    "inductive",
    "abductive",
    "analogical",
    "transcendental",
    "pragmatic",
    "probabilistic",
]
PREMISE_TYPES = ["empirical", "conceptual", "normative", "metaphysical", "methodological"]
QUESTION_TYPES = ["conceptual", "empirical", "normative", "metaphysical", "mixed"]

FALSIFICATION_TEST_KINDS = [
    "counterexample",
    "empirical_prediction",
    "reductio",
    "rival_comparison",
    "edge_case",
    "immunization_check",
    "conceptual_stress",
]
FALSIFICATION_REQUIRED_KINDS = [
    "counterexample",
    "reductio",
    "rival_comparison",
    "edge_case",
    "immunization_check",
]
FALSIFICATION_VERDICTS = ["SURVIVED", "SURVIVED_WITH_DAMAGE", "FALSIFIED"]
FALSIFICATION_SEVERITY = {"SURVIVED": 0, "SURVIVED_WITH_DAMAGE": 1, "FALSIFIED": 2}

DEBATE_EXCHANGES = {
    "semifinal": ["attack", "defense"],
    "final": ["attack", "defense", "closing"],
}

# ---------------------------------------------------------------------------
# Profil mode. Semua angka dapat ditimpa oleh parameter eksplisit yang relevan.
# ---------------------------------------------------------------------------
MODES = {
    "efficient": {
        "description": "Pra-seleksi berbasis skor scouting untuk ronde awal; duel LLM hanya mulai ambang deep review.",
        "gen_batch": 40,
        "scout_batch": 40,
        "early_method": "score",
        "duel_batch": 0,
        "deep_round_threshold": 16,
        "deep_panel": 3,
        "deep_batch": 8,
        "semifinal_panel": 3,
        "final_panel": 3,
        "falsification_panel": 1,
        "dedup_review": False,
        "max_refill_rounds": 1,
    },
    "balanced": {
        "description": "Duel LLM ringkas (1 juri) di ronde awal; panel 3 juri mulai ambang deep review; panel 5 di semifinal/final.",
        "gen_batch": 25,
        "scout_batch": 25,
        "early_method": "llm_single",
        "duel_batch": 20,
        "deep_round_threshold": 32,
        "deep_panel": 3,
        "deep_batch": 4,
        "semifinal_panel": 5,
        "final_panel": 5,
        "falsification_panel": 2,
        "dedup_review": True,
        "max_refill_rounds": 2,
    },
    "full": {
        "description": "Setiap duel dinilai dengan protokol lengkap (steelman + pemeriksaan silang); panel 7 di final.",
        "gen_batch": 20,
        "scout_batch": 20,
        "early_method": "llm_single_full",
        "duel_batch": 8,
        "deep_round_threshold": 64,
        "deep_panel": 3,
        "deep_batch": 4,
        "semifinal_panel": 5,
        "final_panel": 7,
        "falsification_panel": 3,
        "dedup_review": True,
        "max_refill_rounds": 2,
    },
}

DEFAULTS = {
    "mode": "balanced",
    "population": 1000,
    "max_parallel": 5,
    "evidence_mode": "internal",
    "language": "id",
    "resume": True,
}

POPULATION_MIN = 8
POPULATION_MAX = 5000
MIN_VALID_FOR_BRACKET = 4
MIN_FILL_RATIO = 0.9          # refill bila petarung valid < 90% target
REFILL_MARGIN = 1.15          # buat 15% lebih banyak dari defisit
MAX_ATTEMPTS = 3              # percobaan per paket sebelum ditinggalkan
ANCHOR_COUNT = 3              # petarung jangkar untuk kalibrasi scouting
CALIBRATION_CLAMP = 15.0      # batas koreksi kalibrasi (skala 0-100)

# Deduplikasi leksikal: skor = 0.5*Jaccard(unigram) + 0.5*Jaccard(bigram)
DEDUP_AUTO_THRESHOLD = 0.70
DEDUP_REVIEW_THRESHOLD = 0.45
DEDUP_MAX_REVIEW_PAIRS = 300
DEDUP_REVIEW_BATCH = 30

MAX_FIGHTER_WORDS = 900
MAX_FALSIFICATION_CANDIDATES = 4

WINNER_FORMULA = {
    "id": "Pemenang adalah argumen yang paling tahan terhadap rubrik pengujian yang diterapkan dalam simulasi ini.",
    "en": "The winner is the argument most resistant to the testing rubric applied in this simulation.",
}
