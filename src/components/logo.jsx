import React from 'react';
import sinicxLogo from '@/logo/sinicx.svg';
// Served from `public/` as plain relative URLs so the prerendered HTML resolves
// them correctly under a subpath deploy (e.g. /maru/).
const karakuriLogo = 'karakuri_products_LOGO_white.svg';
const clusterLogo = 'clusterlogo_1line_solid_color_dark.svg';

export default class CorporateLogo extends React.Component {
  constructor(props) {
    super(props);
    this.style = {
      sinicx: {
        xs: { height: '12px', margin: '6px' },
        sm: { height: '14px', margin: '7px' },
        lg: { height: '20px', margin: '10px' },
        xl: {
          height: '24px',
          margin: '15px', // minimal margin
          marginTop: '30px',
        },
      },
      karakuri: {
        xs: { height: '12px', margin: '6px' },
        sm: { height: '14px', margin: '7px' },
        lg: { height: '20px', margin: '10px' },
        xl: { height: '70px', margin: '12px' },
      },
      cluster: {
        xs: { height: '12px', margin: '6px' },
        sm: { height: '14px', margin: '7px' },
        lg: { height: '20px', margin: '10px' },
        xl: { height: '60px', margin: '12px' },
      },
    };
  }

  render() {
    const divStyle = { filter: this.props.inverted ? 'invert(100%)' : 'none' };
    const logoStyle = this.style[this.props.name][this.props.size];

    let logoSvg;
    switch (this.props.name) {
      case 'karakuri':
        logoSvg = karakuriLogo;
        break;
      case 'cluster':
        logoSvg = clusterLogo;
        break;
      default:
        logoSvg = sinicxLogo;
        break;
    }

    return (
      <div style={divStyle}>
        <img src={logoSvg} style={logoStyle} />
      </div>
    );
  }
}
