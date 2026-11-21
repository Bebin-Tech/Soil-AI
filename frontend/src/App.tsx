import {lazy,Suspense} from 'react';
import {BrowserRouter,Route,Routes} from 'react-router-dom';
import {AuthProvider} from './contexts/Auth';
import AuthPage from './pages/AuthPage';
import Workspace from './layouts/Workspace';
import {Loading} from './components/Common';
import './styles.css';
import './sidebar.css';
import './theme.css';
const Dashboard=lazy(()=>import('./pages/DashboardPage'));
const Farms=lazy(()=>import('./pages/FarmsPage'));
const Samples=lazy(()=>import('./pages/SamplesPage'));
const SampleForm=lazy(()=>import('./pages/SampleForm'));
const SampleDetail=lazy(()=>import('./pages/SampleDetail'));
const Imports=lazy(()=>import('./pages/ImportsPage'));
const Profile=lazy(()=>import('./pages/ProfilePage'));
const Admin=lazy(()=>import('./pages/AdminPage'));
const Reports=lazy(()=>import('./pages/ReportsPage'));
export default function App(){
  return <BrowserRouter><AuthProvider><Suspense fallback={<Loading/>}><Routes>
    {['login','register','forgot','reset'].map(path=><Route key={path} path={`/${path}`} element={<AuthPage/>}/>)}
    <Route element={<Workspace/>}>
      <Route index element={<Dashboard/>}/><Route path="farms" element={<Farms/>}/>
      <Route path="samples" element={<Samples/>}/><Route path="samples/new" element={<SampleForm/>}/>
      <Route path="samples/:id" element={<SampleDetail/>}/><Route path="samples/:id/edit" element={<SampleForm/>}/>
      <Route path="imports" element={<Imports/>}/><Route path="profile" element={<Profile/>}/><Route path="admin" element={<Admin/>}/>
      <Route path="reports" element={<Reports/>}/>
      <Route path="*" element={<div className="panel form-panel"><h2>Page not found</h2><a href="/">Return to workspace</a></div>}/>
    </Route>
  </Routes></Suspense></AuthProvider></BrowserRouter>;
}
