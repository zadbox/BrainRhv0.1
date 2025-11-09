import { useNavigate } from 'react-router-dom';
import { Building2, FolderOpen, FileText, Target, BarChart3, BarChart } from 'lucide-react';
import { Button } from '../components/ui/button';

interface DashboardCard {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
  gradient: string;
}

const dashboardCards: DashboardCard[] = [
  {
    title: 'Companies',
    description: 'Manage your client companies',
    icon: Building2,
    path: '/enterprises',
    gradient: 'from-[#ff9776] via-[#ff70d6] to-[#8b77ff]',
  },
  {
    title: 'Projects',
    description: 'Manage your recruiting projects',
    icon: FolderOpen,
    path: '/projects',
    gradient: 'from-[#7f7bff] via-[#8ec5ff] to-[#42a1ff]',
  },
  {
    title: 'CV Library',
    description: 'Upload and manage your resumes',
    icon: FileText,
    path: '/cvs',
    gradient: 'from-[#53f3c3] via-[#5edbdc] to-[#5f9dff]',
  },
  {
    title: 'Matching',
    description: 'Launch intelligent matching',
    icon: Target,
    path: '/matching',
    gradient: 'from-[#ff8a73] via-[#ff64b9] to-[#6e7bff]',
  },
  {
    title: 'Results',
    description: 'Review your matching outcomes',
    icon: BarChart3,
    path: '/results',
    gradient: 'from-[#7adfff] via-[#8da4ff] to-[#c173ff]',
  },
];

const highlights = [
  {
    title: 'Enterprise-grade pipeline',
    description: 'Secure matching workflows engineered for regulated industries.'
  },
  {
    title: 'AI-assisted insights',
    description: 'Explainable scoring and HR appreciations for every shortlist.'
  },
  {
    title: 'Actionable analytics',
    description: 'Follow conversion metrics and candidate funnels in real time.'
  },
];

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-10 rounded-3xl bg-[#0c0c12] p-10 text-gray-100 shadow-[0_45px_140px_-90px_rgba(90,80,255,0.7)] overflow-hidden">
      <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#ff8a7a] via-[#ff66d3] to-[#6f7fff] p-10 text-white shadow-[0px_20px_60px_-30px_rgba(116,71,255,0.9)]">
          <span className="absolute -top-24 -right-12 h-52 w-52 rounded-full bg-white/10 blur-3xl" aria-hidden="true" />
          <span className="absolute bottom-[-60px] left-[-80px] h-72 w-72 rounded-full bg-white/10 blur-3xl" aria-hidden="true" />
          <div className="relative space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-white/80">
              Brain HR+ • Talent Intelligence Suite
            </div>
            <div className="space-y-3">
              <h1 className="text-4xl font-semibold tracking-tight">Pilot your corporate matching strategy with clarity.</h1>
              <p className="max-w-xl text-base text-white/80">
                All your candidates, projects and insights unified in one executive dashboard. Launch curated matches, monitor performance and infuse your recruiting rituals with a consistent, premium experience.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button size="lg" className="bg-white text-black hover:bg-white/90" onClick={() => navigate('/matching')}>
                Launch matching
              </Button>
              <Button size="lg" variant="outline" className="border-white/40 bg-white/10 text-white hover:bg-white/20" onClick={() => navigate('/results')}>
                View performance
              </Button>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-white/5 bg-white/5 p-8 backdrop-blur-sm">
          <div className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-white/50">
            <BarChart className="h-4 w-4" />
            Operating overview
          </div>
          <div className="mt-6 space-y-6">
            {highlights.map((item) => (
              <div key={item.title} className="space-y-1">
                <p className="text-sm font-semibold text-white/80">{item.title}</p>
                <p className="text-sm text-white/60">{item.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/65">
            Governance-ready artefacts, granular audit trails and explainable AI appreciations help your HRBP teams drive executive decisions with confidence.
          </div>
        </div>
      </div>

      <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {dashboardCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.path}
              className={`group relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br ${card.gradient} p-[1px]`}
            >
              <div className="flex h-full flex-col justify-between rounded-[calc(1.5rem-2px)] bg-black/60 p-6 transition duration-200 group-hover:bg-black/50" onClick={() => navigate(card.path)} role="button" tabIndex={0} onKeyPress={(event) => {
                if (event.key === 'Enter' || event.key === ' ') navigate(card.path);
              }}>
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <h2 className="text-xl font-semibold text-white">{card.title}</h2>
                    <p className="text-sm text-white/70">{card.description}</p>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/15 text-white">
                    <Icon className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-6 flex items-center gap-2 text-sm font-semibold text-white/80">
                  Explore
                  <span className="text-white/60 transition group-hover:translate-x-1">→</span>
                </div>
              </div>
            </div>
          );
        })}
      </section>

      
    </div>
  );
};
