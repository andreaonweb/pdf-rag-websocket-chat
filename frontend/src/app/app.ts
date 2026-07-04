import { Component } from '@angular/core';
import { ChatPage } from './features/chat/chat-page/chat-page';

@Component({
  selector: 'app-root',
  imports: [ChatPage],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
