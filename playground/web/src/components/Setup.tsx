import { motion } from "motion/react";
import GlitchText from "./GlitchText";
import { ShimmerButton } from "./ShimmerButton";
import { IconLogin, IconPlugConnected, IconGitPullRequest } from "@tabler/icons-react";

export function Setup() {
  const steps = [
    {
      icon: <IconLogin size={32} stroke={1.5} color="#8ab4ff" />,
      title: "Sign in",
      description: "Log into the GitOwl Dashboard using your GitHub account."
    },
    {
      icon: <IconPlugConnected size={32} stroke={1.5} color="#8ab4ff" />,
      title: "Install the App",
      description: "Click 'Connect Repository' and authorize GitOwl on your chosen repos."
    },
    {
      icon: <IconGitPullRequest size={32} stroke={1.5} color="#8ab4ff" />,
      title: "Open a Pull Request",
      description: "GitOwl automatically reviews the code and posts a professional, structured comment."
    }
  ];

  return (
    <section className="setup" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <GlitchText
        speed={1}
        enableShadows={true}
        enableOnHover={false}
        className="setup-heading"
      >
        Install in seconds
      </GlitchText>
      <p style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto 3rem auto', color: '#9ca3af' }}>
        GitOwl is a GitHub App. There's no python package to install, and no workflow files to maintain. Just 3 clicks:
      </p>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
        gap: '2rem', 
        width: '100%', 
        maxWidth: '1000px',
        marginBottom: '4rem' 
      }}>
        {steps.map((step, index) => (
          <motion.div 
            key={index}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.15, duration: 0.5 }}
            style={{
              background: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '16px',
              padding: '2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <div style={{
              background: 'rgba(138, 180, 255, 0.1)',
              padding: '1rem',
              borderRadius: '50%',
              marginBottom: '1.5rem'
            }}>
              {step.icon}
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.75rem', marginTop: 0 }}>
              {index + 1}. {step.title}
            </h3>
            <p style={{ color: '#94a3b8', margin: 0, lineHeight: 1.5, fontSize: '0.95rem' }}>
              {step.description}
            </p>
          </motion.div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <ShimmerButton 
          href="https://gitowl-dashboard.vercel.app" 
          background="#2ea043" 
          shimmerColor="#3fb950"
        >
          Sign in to GitHub
        </ShimmerButton>
      </div>
    </section>
  );
}
