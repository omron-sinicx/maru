import React from 'react';
import { render } from 'react-dom';

const ProjectCard = ({ title, img, description, journal, url }) => (
  <a
    href={url}
    target="_blank"
    className="uk-card uk-card-default uk-grid-collapse uk-margin uk-link-toggle"
    data-uk-grid
  >
    <div className="uk-card-media-left uk-cover-container uk-width-1-3@s">
      <img src={img} alt="" data-uk-cover />
      <canvas width="200" height="200"></canvas>
    </div>
    <div className="uk-width-2-3@s">
      <div className="uk-card-body">
        <div className="uk-card-badge uk-label">{journal}</div>
        <h6>{title}</h6>
        <p>{description}</p>
      </div>
    </div>
  </a>
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
              title={project.title}
              img={project.img}
              description={project.description}
              journal={project.journal}
              url={project.url}
            />
          );
        })}
      </div>
    ) : null;
  }
}
