import React from 'react';

const ProjectCard = ({ title, img, description, journal, url, award }) => (
  <div data-uk-scrollspy="cls: uk-animation-fade; delay: 200; repeat: true">
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className={`project-card${award ? ' is-award' : ''}`}
    >
      <div className="project-card-media">
        <img src={img} alt="" loading="lazy" />
      </div>
      <div className="project-card-body">
        <div className="project-card-meta">
          <span className="project-card-venue">{journal}</span>
          {award && <span className="project-card-award">🏆 {award}</span>}
        </div>
        <h3 className="project-card-title">{title}</h3>
        <p className="project-card-desc">{description}</p>
      </div>
    </a>
  </div>
);

export default class Projects extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return this.props.projects ? (
      <div className="uk-section">
        <h2 className="uk-heading-line uk-text-center">
          Projects powered by maru
        </h2>
        <p>
          maru is used across diverse fields, including not only HCI
          applications but also Robotics and Machine Learning.
        </p>
        {this.props.projects.map((project, idx) => {
          return (
            <ProjectCard
              key={'project-' + idx}
              title={project.title}
              img={project.img}
              description={project.description}
              journal={project.journal}
              url={project.url}
              award={project.award}
            />
          );
        })}
      </div>
    ) : null;
  }
}
