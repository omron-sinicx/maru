import React from 'react';
import { render } from 'react-dom';
import UIkit from 'uikit';
import { FaCopy } from 'react-icons/fa';

const CopyButton = ({ text }) => {
  const copyToClipboard = () => {
    const tt = document.querySelector('.tooltip');
    navigator.clipboard.writeText(text).then(
      () => {
        UIkit.tooltip(tt, { title: 'Copied!' }).show();
        console.log('copied:');
      },
      (err) => {
        console.error('failed to copy text:', err);
      }
    );
  };
  return (
    <button
      className="tooltip uk-align-right uk-text-emphasis"
      onClick={copyToClipboard}
      style={{
        border: 'none',
        background: 'transparent',
        color: '#333',
        cursor: 'pointer',
      }}
    >
      <FaCopy size={18} style={{ color: '#333' }} />
    </button>
  );
};

export default class Citation extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="uk-section">
        <h2 className="uk-heading-line uk-text-center">Citation</h2>
        <p>maru was first introduced and used in the following paper:</p>
        <pre
          className="uk-padding-small"
          style={{
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            overflowWrap: 'break-word',
          }}
        >
          <CopyButton text={this.props.bibtex} />
          <code>{this.props.bibtex}</code>
        </pre>
      </div>
    );
  }
}
