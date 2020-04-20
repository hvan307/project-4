import React from 'react'
import ReactDOM from 'react-dom'
import { HashRouter, Switch, Route } from 'react-router-dom'

import NavbarDrawer from './Common/NavbarDrawer'
import Register from './User/Register'
import Login from './User/Login'
import ChatRoom from './Common/ChatRoom'
import PreChat from './Common/PreChat'
import Home from './Common/Home'

const App = () => {
  return <HashRouter>
    <NavbarDrawer />
    <Switch>
      <Route path={'/register'} component={Register} />
      <Route path={'/login'} component={Login} />
      {/* <Route path={'/myprofile'} component={MyProfile} />
      <Route path={'/mychats'} component={MyChats} /> */}
      <Route path={'/chatroom'} component={ChatRoom} />
      <Route path={'/'} component={Home} />
    </Switch>
    <PreChat />
  </HashRouter>
}


ReactDOM.render(
  <App />,
  document.getElementById('root')
)