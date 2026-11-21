import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {describe,it,expect,vi} from 'vitest';
import AuthPage from './AuthPage';
import {api,saveSession} from '../services/api';
vi.mock('../services/api',()=>({api:{post:vi.fn()},saveSession:vi.fn(),errorMessage:()=> 'Invalid credentials'}));
vi.mock('../contexts/Auth',()=>({useAuth:()=>({user:null})}));
describe('Authentication',()=>{
  it('submits login credentials and stores the returned session',async()=>{
    vi.mocked(api.post).mockResolvedValueOnce({data:{access_token:'token'}});
    render(<MemoryRouter initialEntries={['/login']}><AuthPage/></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'farmer@example.com'}});
    fireEvent.change(screen.getByLabelText('Password'),{target:{value:'long-password'}});
    fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
    await waitFor(()=>expect(saveSession).toHaveBeenCalledWith({access_token:'token'}));
  });
  it('shows API errors without navigating away',async()=>{
    vi.mocked(api.post).mockRejectedValueOnce(new Error('no'));
    render(<MemoryRouter initialEntries={['/login']}><AuthPage/></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'farmer@example.com'}});
    fireEvent.change(screen.getByLabelText('Password'),{target:{value:'bad-password'}});
    fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
  });
});
