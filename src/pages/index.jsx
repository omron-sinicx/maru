import React from 'react';
import { ViteReactSSG } from 'vite-react-ssg/single-page';
import { Head } from 'vite-react-ssg';

import Header from '@/components/header.jsx';
import Overview from '@/components/overview.jsx';
import Video from '@/components/video.jsx';
import Body from '@/components/body.jsx';
import Contact from '@/components/contact.jsx';
import Footer from '@/components/footer.jsx';
import Citation from '@/components/citation.jsx';
import SpeakerDeck from '@/components/speakerdeck.jsx';
import Projects from '@/components/projects.jsx';
import data from '../../template.yaml';

import '@/js/styles.js';

class Template extends React.Component {
  componentDidMount() {
    // UIkit touches `document`, so it must only run on the client (never
    // during the static build/SSG pass). Dynamic-import it after mount.
    (async () => {
      const { default: UIkit } = await import('uikit');
      const { default: Icons } = await import('uikit/dist/js/uikit-icons');
      UIkit.use(Icons);
    })();
  }

  render() {
    return (
      <div>
        <Head>
          <title>{data.title}</title>
          <meta property="og:site_name" content={data.organization} />
          <meta property="og:type" content="article" />
          <meta property="og:title" content={data.title} />
          <meta property="og:description" content={data.description} />
          <meta property="og:image" content={data.image} />
          <meta property="og:image:alt" content={data.description} />
          <meta property="og:image:width" content="1200" />
          <meta property="og:image:height" content="600" />
          <meta property="og:url" content={data.url} />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content={data.title} />
          <meta name="twitter:image:src" content={data.image} />
          <meta name="twitter:description" content={data.description} />
          <meta name="twitter:url" content={data.url} />
          <meta name="twitter:site" content={data.twitter} />
        </Head>
        <Header
          title={data.title}
          conference={data.conference}
          authors={data.authors}
          affiliations={data.affiliations}
          meta={data.meta}
          resources={data.resources}
          theme={data.theme}
          header={data.header}
        />
        <Overview
          slideshow={data.slideshow}
          overview={data.overview}
          teaser={data.teaser}
          description={data.description}
        />
        <div className="uk-container uk-container-small">
          <Video video={data.resources.video} />
          <SpeakerDeck dataId={data.speakerdeck} />
          <Body body={data.body} />
          <Contact
            authors={data.authors}
            contact_ids={data.contact_ids}
            resources={data.resources}
          />
          {data.bibtex && <Citation bibtex={data.bibtex} />}
          <Projects projects={data.projects} />
        </div>
        <Footer />
      </div>
    );
  }
}

export const createRoot = ViteReactSSG(<Template />);
