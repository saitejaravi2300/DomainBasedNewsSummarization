import { Digest, SavedTrend } from './types'

export const mockDigest: Digest = {
  digest_id: 'digest-001',
  domain: 'AI & ML',
  days: 7,
  generated_at: new Date().toISOString(),
  total_trends: 6,
  total_articles: 43,
  cached: false,
  trends: [
    {
      trend_id: 1,
      trend_title: 'OpenAI Releases GPT-5 with Reasoning Capabilities',
      tldr: 'GPT-5 introduces chain-of-thought reasoning by default, achieving 94% on graduate-level math benchmarks.',
      summary: `OpenAI has released GPT-5, marking a significant advancement in AI reasoning capabilities. The new model demonstrates unprecedented performance on complex reasoning tasks, including graduate-level mathematics and scientific problem-solving.

The release comes amid intensifying competition in the AI space, with Google and Anthropic racing to match OpenAI's capabilities. Industry analysts suggest this could accelerate enterprise AI adoption significantly.

Initial benchmarks show GPT-5 outperforming previous models by 40% on multi-step reasoning tasks, though questions remain about computational costs and accessibility.`,
      timeline: [
        { date: '2026-03-28', event: 'OpenAI announces GPT-5 at developer conference' },
        { date: '2026-03-30', event: 'Beta access rolls out to API partners' },
        { date: '2026-04-01', event: 'Public availability begins for Plus subscribers' },
      ],
      so_what: 'Enterprise teams should evaluate GPT-5 for complex analysis tasks where previous models fell short on multi-step reasoning.',
      signal_score: 9,
      contrast: 'While OpenAI emphasizes safety improvements, some researchers argue the rapid release timeline leaves insufficient time for thorough safety testing.',
      key_entities: ['OpenAI', 'GPT-5', 'Sam Altman', 'Microsoft'],
      source_count: 12,
      articles: [
        { title: 'OpenAI Unveils GPT-5 with Advanced Reasoning', source: 'TechCrunch', url: '#', published: '2026-03-28' },
        { title: 'GPT-5 Benchmarks Show Major Leap', source: 'Ars Technica', url: '#', published: '2026-03-29' },
        { title: 'What GPT-5 Means for Enterprise AI', source: 'Forbes', url: '#', published: '2026-03-30' },
      ]
    },
    {
      trend_id: 2,
      trend_title: 'EU AI Act Enforcement Begins with First Penalties',
      tldr: 'European regulators issue first fines under AI Act, targeting facial recognition and hiring algorithm providers.',
      summary: `The European Union has begun active enforcement of the AI Act, with regulators issuing the first penalties to companies deploying prohibited AI systems. Two facial recognition providers and one hiring algorithm company face combined fines exceeding €50 million.

This marks a significant shift in global AI governance, as the EU positions itself as the de facto standard-setter for AI regulation. Companies operating in Europe must now demonstrate compliance or face substantial penalties.

Legal experts predict this will create a "Brussels Effect" similar to GDPR, where companies adopt EU standards globally to simplify compliance.`,
      timeline: [
        { date: '2026-03-25', event: 'EU announces first enforcement actions under AI Act' },
        { date: '2026-03-27', event: 'Three companies receive formal penalty notices' },
        { date: '2026-04-01', event: 'Appeals process begins for affected companies' },
      ],
      so_what: 'Organizations deploying AI in Europe should audit high-risk systems immediately and document compliance measures before Q3.',
      signal_score: 8,
      contrast: null,
      key_entities: ['European Union', 'AI Act', 'Clearview AI', 'HireVue'],
      source_count: 8,
      articles: [
        { title: 'EU Issues First AI Act Penalties', source: 'Reuters', url: '#', published: '2026-03-25' },
        { title: 'What the AI Act Enforcement Means', source: 'Financial Times', url: '#', published: '2026-03-26' },
      ]
    },
    {
      trend_id: 3,
      trend_title: 'Anthropic Secures $4B for Agentic AI Development',
      tldr: 'Anthropic raises $4 billion Series D to accelerate development of autonomous AI agents for enterprise.',
      summary: `Anthropic has closed a $4 billion Series D funding round, the largest in AI history, to develop next-generation autonomous AI agents. The round values the company at $60 billion, making it the most valuable AI startup globally.

The funding will primarily support "Constitutional AI 2.0," Anthropic's framework for building AI agents that can operate autonomously while maintaining alignment with human values. CEO Dario Amodei outlined plans to deploy enterprise agents by 2027.

Investors include Google, Spark Capital, and several sovereign wealth funds, reflecting growing confidence in Anthropic's safety-first approach to AI development.`,
      timeline: [
        { date: '2026-03-26', event: 'Anthropic announces Series D funding' },
        { date: '2026-03-28', event: 'Company reveals agentic AI roadmap' },
        { date: '2026-03-30', event: 'New research lab opens in London' },
      ],
      so_what: 'The massive funding signals that agentic AI is the next major battleground—teams should begin exploring agent architectures now.',
      signal_score: 8,
      contrast: 'While Anthropic emphasizes safety, critics question whether any company can responsibly develop autonomous agents at this pace.',
      key_entities: ['Anthropic', 'Dario Amodei', 'Google', 'Claude'],
      source_count: 10,
      articles: [
        { title: 'Anthropic Raises Record $4B Round', source: 'Bloomberg', url: '#', published: '2026-03-26' },
        { title: 'Inside Anthropic\'s Agentic AI Plans', source: 'The Information', url: '#', published: '2026-03-27' },
      ]
    },
    {
      trend_id: 4,
      trend_title: 'Apple Intelligence Expands to Third-Party Apps',
      tldr: 'Apple opens Siri\'s on-device AI to developers, enabling private AI features in any iOS app.',
      summary: `Apple has announced the expansion of Apple Intelligence to third-party developers, allowing any iOS app to leverage the company's on-device AI capabilities. This marks Apple's most significant AI platform play since the original App Store launch.

The new APIs enable developers to integrate features like summarization, writing assistance, and image understanding without sending data to external servers. Apple emphasized this maintains their privacy-first approach while democratizing AI capabilities.

Early partners include Microsoft, Adobe, and Notion, with broader availability expected at WWDC 2026.`,
      timeline: [
        { date: '2026-03-27', event: 'Apple announces developer APIs for Apple Intelligence' },
        { date: '2026-03-29', event: 'Beta SDK available to registered developers' },
        { date: '2026-04-02', event: 'First third-party apps begin testing' },
      ],
      so_what: 'iOS developers should evaluate Apple Intelligence APIs for features currently relying on cloud AI to improve privacy and reduce latency.',
      signal_score: 7,
      contrast: null,
      key_entities: ['Apple', 'Siri', 'Apple Intelligence', 'iOS'],
      source_count: 7,
      articles: [
        { title: 'Apple Opens AI Platform to Developers', source: 'The Verge', url: '#', published: '2026-03-27' },
        { title: 'What Apple Intelligence Means for Apps', source: 'Wired', url: '#', published: '2026-03-28' },
      ]
    },
    {
      trend_id: 5,
      trend_title: 'AI Chip Shortage Eases as New Fabs Come Online',
      tldr: 'NVIDIA and TSMC capacity expansions cut AI chip lead times from 6 months to 8 weeks.',
      summary: `The global AI chip shortage is finally easing as new fabrication facilities from NVIDIA, TSMC, and Intel come online. Lead times for high-end AI accelerators have dropped from six months to approximately eight weeks, marking a significant improvement for AI infrastructure deployment.

This shift could accelerate enterprise AI adoption, as companies no longer need to wait months for hardware. Cloud providers are already adjusting pricing in response to improved supply.

Analysts caution that demand continues to grow rapidly, and the equilibrium may be temporary as agentic AI workloads require significantly more compute.`,
      timeline: [
        { date: '2026-03-20', event: 'TSMC Arizona fab reaches full production' },
        { date: '2026-03-25', event: 'NVIDIA announces improved H200 availability' },
        { date: '2026-04-01', event: 'Cloud providers begin price adjustments' },
      ],
      so_what: 'Now is an opportune time to secure AI infrastructure—negotiate contracts before demand from agentic AI potentially tightens supply again.',
      signal_score: 6,
      contrast: 'Industry analysts disagree on whether the supply improvement is sustainable, with some predicting renewed shortages by Q4.',
      key_entities: ['NVIDIA', 'TSMC', 'Intel', 'H200'],
      source_count: 6,
      articles: [
        { title: 'AI Chip Shortage Finally Easing', source: 'Wall Street Journal', url: '#', published: '2026-03-25' },
        { title: 'What Improved Chip Supply Means', source: 'Semiconductor Weekly', url: '#', published: '2026-03-26' },
      ]
    },
    {
      trend_id: 6,
      trend_title: 'AI-Generated Content Detection Advances with New Standards',
      tldr: 'Coalition of tech giants releases unified watermarking standard for detecting AI-generated images and text.',
      summary: `A coalition including Google, Microsoft, Adobe, and OpenAI has released C2PA 2.0, a unified standard for watermarking AI-generated content. The standard embeds cryptographic signatures in images, videos, and text that survive most editing and compression.

Major platforms including YouTube, Instagram, and X have committed to implementing detection by Q3 2026. The move addresses growing concerns about misinformation and deepfakes ahead of the US midterm elections.

Critics note that the standard only works for compliant tools, leaving open-source AI models as potential loopholes.`,
      timeline: [
        { date: '2026-03-24', event: 'C2PA 2.0 standard officially released' },
        { date: '2026-03-26', event: 'Major platforms announce adoption timeline' },
        { date: '2026-03-29', event: 'First tools begin implementing watermarks' },
      ],
      so_what: 'Content teams should prepare for mandatory AI disclosure—audit your AI-generated content pipeline and implement watermarking tools.',
      signal_score: 5,
      contrast: null,
      key_entities: ['C2PA', 'Google', 'Microsoft', 'Adobe', 'OpenAI'],
      source_count: 5,
      articles: [
        { title: 'Tech Giants Unite on AI Watermarking', source: 'MIT Technology Review', url: '#', published: '2026-03-24' },
        { title: 'C2PA 2.0 Explained', source: 'Ars Technica', url: '#', published: '2026-03-25' },
      ]
    }
  ]
}

export const mockDigestHistory: { id: string; domain: string; date: string; trends: number }[] = [
  { id: 'digest-001', domain: 'AI & ML', date: '2026-04-02', trends: 6 },
  { id: 'digest-002', domain: 'Finance', date: '2026-04-01', trends: 5 },
  { id: 'digest-003', domain: 'AI & ML', date: '2026-03-28', trends: 7 },
  { id: 'digest-004', domain: 'Climate', date: '2026-03-25', trends: 4 },
  { id: 'digest-005', domain: 'Healthcare', date: '2026-03-22', trends: 6 },
]

export const mockSavedTrends: SavedTrend[] = [
  {
    id: 'saved-001',
    user_id: 'user-001',
    digest_id: 'digest-001',
    trend_id: 1,
    saved_at: '2026-04-02T10:30:00Z',
    trend: mockDigest.trends[0],
    domain: 'AI & ML'
  },
  {
    id: 'saved-002',
    user_id: 'user-001',
    digest_id: 'digest-001',
    trend_id: 2,
    saved_at: '2026-04-01T14:20:00Z',
    trend: mockDigest.trends[1],
    domain: 'AI & ML'
  }
]

export const mockUser = {
  id: 'user-001',
  email: 'professional@company.com',
  name: 'Alex Morgan',
  avatar_url: null,
  preferences: {
    default_domain: 'ai',
    default_days: 7,
    daily_digest_enabled: true,
    daily_digest_time: '08:00',
    daily_digest_domain: 'ai'
  },
  created_at: '2026-01-15T00:00:00Z',
  last_active_at: new Date().toISOString()
}
