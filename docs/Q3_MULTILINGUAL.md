# Q3 — Philippines and Indonesia

## What was configured

| Market | Sector | Files |
| --- | --- | --- |
| Philippines | Life insurance / bancassurance | `data/philippines_config.json`, `backend/multilingual/philippines.py`, `data/kb/philippines/` |
| Indonesia | Multifinance | `data/indonesia_config.json`, `backend/multilingual/indonesia.py`, `data/kb/indonesia/` |

Knowledge for each market is written in that market's wording and retrieved with a source prefix. There is no translation call.

## Localization, not translation

Philippines examples in the config:

1. Greeting uses Taglish, a first name, and a bank-link time check.
2. The premium objection uses `gets ko`, `swak`, `po`, and `lapse`, and refuses a forced sale.
3. The payment line keeps `premium`, `bank referral`, `beneficiary`, `rider`, `lapse`, and `coverage`, and says the product is not a deposit.

Indonesia examples:

1. The greeting uses `cicilan` and `jatuh tempo`, and asks permission before talking about money.
2. The denda objection refuses a waiver and offers a tenor callback. It does not threaten.
3. The payment line corrects the local mix-up that a paid DP cancels the next angsuran.

Each example in the JSON has `why_localization` and the literal English rendering it is not using.

## Code-switching

`backend/multilingual/detect.py` labels Taglish, Filipino/Tagalog markers, English, formal Indonesian, colloquial Indonesian, and a few Javanese forms. The last evaluation run had zero detector mismatches on the six labeled sentences in `results/multilingual_results.json`. That is a text rule check. It is not an ASR score.

The Taglish rider question retrieved `kb_ph_payment_c001` and answered in Tagalog/Taglish. The colloquial Indonesian denda question stayed in Indonesian and did not mention prison or a threat.

## ASR report

| Item | Value |
| --- | --- |
| Provider | `mock` |
| Model | NOT MEASURED |
| Languages configured | English, Filipino/Tagalog markers, Bahasa Indonesia |
| Code-switching | Text detector only |
| Approximate quality | NOT MEASURED |
| Observed ASR errors | NOT MEASURED |
| ASR latency | NOT MEASURED |

No ASR key was present. Mock ASR returns text it was given.

## Regional accent

Phrase: `Nyuwun sewu, cicilane telat, bayare piye?`

Region: Javanese-influenced Indonesian, Central Java, outside Jakarta.

Expected meaning: excuse me, the installment is late, how do I pay?

Actual ASR transcript: `NOT MEASURED`.

Observed ASR error: `NOT MEASURED`.

If confidence were low, the bot stays in Indonesian: `Maaf, saya kurang jelas mendengarnya. Bisa diulang pelan-pelan?`

The lexicon rewrite of that already-transcribed phrase is `permisi, cicilan telat, pembayaran bagaimana?` This is not accent recognition.

## TTS

On this Mac, `say -v '?'` includes Damayanti (`id_ID`) and does not include a Filipino or Tagalog voice.

- `recordings/q3_indonesia/greeting_damayanti.aiff` is Damayanti reading one synthetic sentence.
- No Filipino TTS sample was generated, because substituting an English voice and calling it Filipino would be misleading.
- Server TTS remains mock and returns no audio bytes.
- Speaking quality and TTS latency are NOT MEASURED.

## Fallback

Philippines fallback stays in Taglish/Filipino. Indonesia uses a formal or colloquial fallback based on register. Neither path switches the refusal into the English health fallback.
