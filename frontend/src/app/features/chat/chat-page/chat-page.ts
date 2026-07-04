import { Component, inject, signal } from '@angular/core';
import { ChatWebsocket } from '../../../core/websocket/chat-websocket';
import { ChatMessage } from '../../../shared/models/chat-message.model';
import { MessageList } from '../message-list/message-list';
import { MessageInput } from '../message-input/message-input';

@Component({
  selector: 'app-chat-page',
  imports: [MessageList, MessageInput],
  templateUrl: './chat-page.html',
  styleUrl: './chat-page.scss',
})
export class ChatPage {
  // inject() (not constructor injection) so the field initializer order
  // below is guaranteed: this field runs before `connectionStatus` reads it.
  private readonly chatWebsocket = inject(ChatWebsocket);

  readonly messages = signal<ChatMessage[]>([]);
  readonly isWaitingForResponse = signal(false);
  readonly connectionStatus = this.chatWebsocket.connectionStatus;

  constructor() {
    this.chatWebsocket.messages$.subscribe((text) => {
      this.messages.update((current) => [
        ...current,
        { role: 'assistant', text, timestamp: new Date() },
      ]);
      this.isWaitingForResponse.set(false);
    });
  }

  onSend(question: string): void {
    this.messages.update((current) => [
      ...current,
      { role: 'user', text: question, timestamp: new Date() },
    ]);
    this.isWaitingForResponse.set(true);
    this.chatWebsocket.send(question);
  }
}
