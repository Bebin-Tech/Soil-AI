import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {it,expect,vi,afterEach} from 'vitest';
import AuthPage from './AuthPage';
import i18n from '../i18n';
vi.mock('../contexts/Auth',()=>({useAuth:()=>({user:null})}));
afterEach(async()=>{await i18n.changeLanguage('en');});
it('switches English/Tamil without losing unsaved form data',async()=>{
  render(<MemoryRouter initialEntries={['/register']}><AuthPage/></MemoryRouter>);
  fireEvent.change(screen.getByLabelText('Full name'),{target:{value:'Farmer Draft'}});
  fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'draft@example.com'}});
  fireEvent.change(screen.getByRole('combobox',{name:'Language / மொழி'}),{target:{value:'ta'}});
  await waitFor(()=>expect(screen.getByText('கணக்கை உருவாக்கவும்',{selector:'button'})).toBeInTheDocument());
  expect(screen.getByLabelText('முழுப் பெயர்')).toHaveValue('Farmer Draft');
  expect(screen.getByLabelText('மின்னஞ்சல் முகவரி')).toHaveValue('draft@example.com');
});
