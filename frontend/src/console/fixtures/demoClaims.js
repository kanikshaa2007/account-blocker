// Development-only demo dataset. Never mixed silently with production data:
// callers must branch on isDemoMode() and render <DemoBanner />.
//
// Items marked with source_dataset come from the downloaded dataset
// (C:\Users\kanik\Downloads\fake-real data\master_fake_real_clean.csv).
export const DEMO_CLAIMS = [
  {
    id: 'demo-x-1001', platform: 'x', postId: 'x1001', language: 'en', contentType: 'text',
    text: 'Viral: Government of India to shut down UPI payments from tonight due to security breach.',
    claim: 'UPI payments will be shut down tonight by the Government of India.',
    author: '@viral_alerts_in', followers: 48200, postedAt: '2026-10-15T14:32:00+05:30', ingestedAt: '2026-10-15T14:35:00+05:30',
    status: 'awaiting_review', tier: 'urgent', score: 0.84, harm: 0.9, uncertainty: 0.7, spread: 0.85, complexity: 0.3,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility'], deferred: [],
    evidence: [
      { title: 'PIB Fact Check: No decision to discontinue UPI', publisher: 'PIB Fact Check', url: 'https://factcheck.pib.gov.in/upi-2026', publishedAt: '2026-10-15T10:00:00+05:30', retrievedAt: '2026-10-15T14:40:00+05:30', type: 'fact-check', language: 'en', excerpt: 'The claim that UPI will be discontinued is fake. UPI services continue to operate normally.', relation: 'refutes', reliability: 'official' }
    ],
    verdict: 'false_misleading', notes: 'Matches PIB refutation verbatim. High reshare velocity in first hour.'
  },
  {
    id: 'demo-ig-1002', platform: 'instagram', postId: 'ig2002', language: 'hi', contentType: 'video',
    text: 'Reel: PM-KISAN ka paisa rok diya gaya — sarkari order viral (Government order claims PM-KISAN funds blocked).',
    claim: 'PM-KISAN installment funds have been blocked by government order.',
    author: '@desh_updates', followers: 128000, postedAt: '2026-10-15T09:12:00+05:30', ingestedAt: '2026-10-15T09:20:00+05:30',
    status: 'in_progress', tier: 'high', score: 0.71, harm: 0.7, uncertainty: 0.8, spread: 0.66, complexity: 0.6,
    spreadEstimated: true, workers: ['video_forensics', 'text_verifier', 'multilingual_retriever'], deferred: ['evidence_synthesizer'],
    evidence: [],
    verdict: null, notes: ''
  },
  {
    id: 'demo-yt-1003', platform: 'youtube', postId: 'yt3003', language: 'en', contentType: 'video',
    text: 'Video: "RBI bans Rs 500 notes again from November" — 240k views in 6 hours.',
    claim: 'RBI will ban Rs 500 notes from November.',
    author: 'Bharat News Daily', followers: 89000, postedAt: '2026-10-14T18:00:00+05:30', ingestedAt: '2026-10-14T18:30:00+05:30',
    status: 'queued', tier: 'high', score: 0.66, harm: 0.75, uncertainty: 0.6, spread: 0.7, complexity: 0.6,
    spreadEstimated: false, workers: ['video_forensics', 'text_verifier'], deferred: ['source_credibility'],
    evidence: [
      { title: 'RBI press release archive: no such notification', publisher: 'Reserve Bank of India', url: 'https://rbi.org.in/press', publishedAt: '', retrievedAt: '2026-10-14T19:00:00+05:30', type: 'official', language: 'en', excerpt: 'No notification regarding withdrawal of Rs 500 notes found in recent releases.', relation: 'context', reliability: 'official' }
    ],
    verdict: null, notes: ''
  },
  {
    id: 'demo-x-1004', platform: 'x', postId: 'x1004', language: 'ta', contentType: 'text',
    text: 'Chennai corporation announces free housing for all flood-affected families — apply via link.',
    claim: 'Chennai corporation announced free housing for all flood-affected families.',
    author: '@chennai_first', followers: 3200, postedAt: '2026-10-13T11:00:00+05:30', ingestedAt: '2026-10-13T11:05:00+05:30',
    status: 'new', tier: 'normal', score: 0.44, harm: 0.5, uncertainty: 0.7, spread: 0.2, complexity: 0.3,
    spreadEstimated: true, workers: ['text_verifier', 'multilingual_retriever'], deferred: [],
    evidence: [], verdict: null, notes: ''
  },
  {
    id: 'demo-x-1005', platform: 'x', postId: 'x1005', language: 'en', contentType: 'link',
    text: 'Blog: Aadhaar data of 80 crore Indians leaked, download sample here.',
    claim: 'Aadhaar data of 80 crore Indians has been leaked.',
    author: '@databreach_watch', followers: 15600, postedAt: '2026-10-12T08:00:00+05:30', ingestedAt: '2026-10-12T08:10:00+05:30',
    status: 'completed', tier: 'urgent', score: 0.81, harm: 0.95, uncertainty: 0.5, spread: 0.8, complexity: 0.4,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility', 'evidence_synthesizer'], deferred: [],
    evidence: [
      { title: 'UIDAI statement: no breach of CIDR detected', publisher: 'UIDAI', url: 'https://uidai.gov.in/statement-oct-2026', publishedAt: '2026-10-12T12:00:00+05:30', retrievedAt: '2026-10-12T12:30:00+05:30', type: 'official', language: 'en', excerpt: 'UIDAI states the Central Identities Data Repository remains secure; sample data appears fabricated.', relation: 'refutes', reliability: 'official' }
    ],
    verdict: 'false_misleading', notes: 'Reviewed by two analysts. Platform report filed.'
  },
  {
    id: 'demo-x-1006', platform: 'x', postId: 'x1006', language: 'en', contentType: 'image',
    text: 'Photo: flooded Delhi metro station, "taken this morning". Image metadata shows 2023 monsoon.',
    claim: 'Delhi metro station flooded this morning.',
    author: '@weather_pix', followers: 8700, postedAt: '2026-10-11T07:00:00+05:30', ingestedAt: '2026-10-11T07:08:00+05:30',
    status: 'completed', tier: 'normal', score: 0.38, harm: 0.3, uncertainty: 0.4, spread: 0.35, complexity: 0.5,
    spreadEstimated: false, workers: ['image_forensics', 'text_verifier'], deferred: [],
    evidence: [
      { title: 'Original photo credited to 2023 monsoon coverage', publisher: 'News archive', url: 'https://example.org/archive-2023-flood', publishedAt: '2023-07-10T00:00:00+05:30', retrievedAt: '2026-10-11T08:00:00+05:30', type: 'news', language: 'en', excerpt: 'Same image published during July 2023 monsoon flooding.', relation: 'refutes', reliability: 'medium' }
    ],
    verdict: 'verified', notes: 'Image forensics confirmed reuse; location genuine, date false.'
  },
  // ===== Dataset items (source_dataset: LIAR / India_MythFacts) =====
  {
    id: 'ds-liar-001', platform: 'x', postId: 'liar_dwayne_001', language: 'en', contentType: 'text',
    text: 'Says the Annies List political group supports third-trimester abortions on demand.',
    claim: 'The Annies List political group supports third-trimester abortions on demand.',
    author: '@dwayne_bohac', followers: 12400, postedAt: '2026-10-14T08:00:00+05:30', ingestedAt: '2026-10-14T08:05:00+05:30',
    status: 'awaiting_review', tier: 'urgent', score: 0.78, harm: 0.8, uncertainty: 0.6, spread: 0.72, complexity: 0.4,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility'], deferred: [],
    evidence: [
      { title: 'PolitiFact: Annies List abortion claim', publisher: 'PolitiFact', url: 'https://www.politifact.com/factchecks/2020/jun/18/facebook-posts/facebook-post-falsely-claims-independents-californ/', publishedAt: '2026-10-14T09:00:00+05:30', retrievedAt: '2026-10-14T09:30:00+05:30', type: 'fact-check', language: 'en', excerpt: 'Claim rated False — no record of Annies List supporting third-trimester abortions on demand.', relation: 'refutes', reliability: 'official' }
    ],
    verdict: 'false_misleading', notes: 'Dataset source: LIAR (dwayne-bohac). Rated Fake.',
  },
  {
    id: 'ds-liar-002', platform: 'x', postId: 'liar_blog_002', language: 'en', contentType: 'text',
    text: 'Health care reform legislation is likely to mandate free sex change surgeries.',
    claim: 'Health care reform legislation mandates free sex change surgeries.',
    author: '@blog_posting', followers: 8900, postedAt: '2026-10-14T10:15:00+05:30', ingestedAt: '2026-10-14T10:20:00+05:30',
    status: 'awaiting_review', tier: 'high', score: 0.73, harm: 0.85, uncertainty: 0.5, spread: 0.6, complexity: 0.3,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility'], deferred: [],
    evidence: [
      { title: 'Health care reform fact check', publisher: 'FactCheck.org', url: 'https://www.factcheck.org/2010/03/health-care-reform-and-abortion/', publishedAt: '2026-10-14T11:00:00+05:30', retrievedAt: '2026-10-14T11:15:00+05:30', type: 'fact-check', language: 'en', excerpt: 'No provision in the Affordable Care Act mandates free sex change surgeries.', relation: 'refutes', reliability: 'official' }
    ],
    verdict: 'false_misleading', notes: 'Dataset source: LIAR (blog-posting). Rated Fake.',
  },
  {
    id: 'ds-liar-003', platform: 'x', postId: 'liar_romney_003', language: 'en', contentType: 'text',
    text: 'When Mitt Romney was governor of Massachusetts, we didnt just slow the rate of growth of our government.',
    claim: 'Mitt Romney slowed government growth as governor of Massachusetts.',
    author: '@mitt_romney_updates', followers: 45000, postedAt: '2026-10-14T12:00:00+05:30', ingestedAt: '2026-10-14T12:05:00+05:30',
    status: 'awaiting_review', tier: 'normal', score: 0.42, harm: 0.3, uncertainty: 0.4, spread: 0.35, complexity: 0.5,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility'], deferred: [],
    evidence: [
      { title: 'Romney Massachusetts record check', publisher: 'PolitiFact', url: 'https://www.politifact.com/', publishedAt: '2026-10-14T13:00:00+05:30', retrievedAt: '2026-10-14T13:10:00+05:30', type: 'fact-check', language: 'en', excerpt: 'Government spending and workforce grew during Romney tenure — claim rated False.', relation: 'refutes', reliability: 'official' }
    ],
    verdict: 'false_misleading', notes: 'Dataset source: LIAR (mitt-romney). Rated Fake.',
  },
  {
    id: 'ds-liar-004', platform: 'x', postId: 'liar_obama_004', language: 'en', contentType: 'text',
    text: 'Hillary Clinton agrees with John McCain "by voting to give George Bush the benefit of the doubt on Iran."',
    claim: 'Hillary Clinton agrees with John McCain on Iran policy.',
    author: '@obama_archive', followers: 2100000, postedAt: '2026-10-14T14:00:00+05:30', ingestedAt: '2026-10-14T14:05:00+05:30',
    status: 'completed', tier: 'normal', score: 0.31, harm: 0.2, uncertainty: 0.25, spread: 0.15, complexity: 0.4,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility'], deferred: [],
    evidence: [
      { title: 'Clinton-McCain Iran vote check', publisher: 'PolitiFact', url: 'https://www.politifact.com/', publishedAt: '2026-10-14T15:00:00+05:30', retrievedAt: '2026-10-14T15:10:00+05:30', type: 'fact-check', language: 'en', excerpt: 'Hillary Clinton and John McCain voted together on Iran-related legislation.', relation: 'supports', reliability: 'official' }
    ],
    verdict: 'verified', notes: 'Dataset source: LIAR (barack-obama). Rated True.',
  },
  {
    id: 'ds-liar-005', platform: 'x', postId: 'liar_rob_005', language: 'en', contentType: 'text',
    text: 'The Chicago Bears have had more starting quarterbacks in the last 10 years than the total number of tenured UW faculty fired during the last two decades.',
    claim: 'Chicago Bears QBs outnumber fired tenured UW faculty.',
    author: '@sports_fact_check', followers: 18500, postedAt: '2026-10-14T15:30:00+05:30', ingestedAt: '2026-10-14T15:35:00+05:30',
    status: 'completed', tier: 'low', score: 0.25, harm: 0.1, uncertainty: 0.3, spread: 0.05, complexity: 0.4,
    spreadEstimated: false, workers: ['text_verifier'], deferred: [],
    evidence: [],
    verdict: 'verified', notes: 'Dataset source: LIAR (robin-vos). Rated True.',
  },
  {
    id: 'ds-myth-006', platform: 'instagram', postId: 'myth_curd_006', language: 'en', contentType: 'text',
    text: '"Eating curd at night is bad for health" — viral health myth.',
    claim: 'Eating curd at night is bad for health.',
    author: '@india_health_facts', followers: 32000, postedAt: '2026-10-14T16:00:00+05:30', ingestedAt: '2026-10-14T16:05:00+05:30',
    status: 'awaiting_review', tier: 'normal', score: 0.55, harm: 0.4, uncertainty: 0.45, spread: 0.4, complexity: 0.3,
    spreadEstimated: false, workers: ['text_verifier', 'source_credibility'], deferred: [],
    evidence: [
      { title: 'Curd at night health myth busted', publisher: 'India MythFacts', url: 'https://example.org/mythfacts/curd-night', publishedAt: '2026-10-14T16:30:00+05:30', retrievedAt: '2026-10-14T16:40:00+05:30', type: 'fact-check', language: 'en', excerpt: 'No scientific evidence that eating curd at night is harmful for most people.', relation: 'refutes', reliability: 'medium' }
    ],
    verdict: 'false_misleading', notes: 'Dataset source: India_MythFacts. Rated Fake.',
  },
  {
    id: 'ds-myth-007', platform: 'instagram', postId: 'myth_knuckles_007', language: 'en', contentType: 'text',
    text: '"Cracking knuckles will cause arthritis" — common health myth.',
    claim: 'Cracking knuckles causes arthritis.',
    author: '@india_health_facts', followers: 32000, postedAt: '2026-10-14T16:30:00+05:30', ingestedAt: '2026-10-14T16:35:00+05:30',
    status: 'awaiting_review', tier: 'low', score: 0.35, harm: 0.15, uncertainty: 0.3, spread: 0.25, complexity: 0.2,
    spreadEstimated: false, workers: ['text_verifier'], deferred: [],
    evidence: [
      { title: 'Knuckle cracking arthritis study', publisher: 'India MythFacts', url: 'https://example.org/mythfacts/knuckles', publishedAt: '2026-10-14T17:00:00+05:30', retrievedAt: '2026-10-14T17:05:00+05:30', type: 'fact-check', language: 'en', excerpt: 'Multiple studies found no link between knuckle cracking and arthritis.', relation: 'refutes', reliability: 'medium' }
    ],
    verdict: 'false_misleading', notes: 'Dataset source: India_MythFacts. Rated Fake.',
  },
]

export const DEMO_ACTIVITY = [
  { t: '2026-10-15T14:35:00+05:30', label: 'Ingested x1001 (UPI shutdown claim)', tier: 'urgent' },
  { t: '2026-10-15T09:20:00+05:30', label: 'Ingested ig2002 (PM-KISAN reel)', tier: 'high' },
  { t: '2026-10-14T14:05:00+05:30', label: 'Ingested obama_archive (Clinton-McCain Iran claim)', tier: 'normal' },
  { t: '2026-10-14T16:05:00+05:30', label: 'Ingested india_health_facts (curd myth)', tier: 'normal' },
  { t: '2026-10-14T16:35:00+05:30', label: 'Ingested india_health_facts (knuckle cracking myth)', tier: 'low' },
  { t: '2026-10-12T12:30:00+05:30', label: 'UIDAI statement retrieved for x1005', tier: 'urgent' }
]

export const DEMO_ACTIONS = [
  { at: '2026-10-15T15:02:00+05:30', actor: 'analyst', action: 'approve_report', target: 'demo-x-1001', from: 'awaiting_review', to: 'reported', reason: 'PIB refutation confirmed', job: 'job_3' },
  { at: '2026-10-12T13:00:00+05:30', actor: 'analyst', action: 'approve_report', target: 'demo-x-1005', from: 'awaiting_review', to: 'reported', reason: 'UIDAI denial + fabricated sample', job: 'job_1' }
]
