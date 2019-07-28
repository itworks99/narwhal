import React from 'react';
import ReactDOM from 'react-dom';
import 'semantic-ui-css/semantic.min.css';
import Narwhal from './narwhal_web.jsx';
import * as serviceWorker from './serviceWorker';

// ReactDOM.hydrate(<Narwhal />, document.getElementById('root'));
ReactDOM.render(<Narwhal />, document.getElementById('root'));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
// serviceWorker.unregister();
serviceWorker.register();
