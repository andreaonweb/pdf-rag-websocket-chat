import { Injectable, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { WS_URL } from '../../../config/websocket.config';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

@Injectable({ providedIn: 'root' })
export class ChatWebsocket {
  private readonly socket: WebSocket;
  private readonly messagesSubject = new Subject<string>();

  readonly connectionStatus = signal<ConnectionStatus>('connecting');
  readonly messages$ = this.messagesSubject.asObservable();

  constructor() {
    this.socket = new WebSocket(WS_URL);

    this.socket.addEventListener('open', () => {
      this.connectionStatus.set('connected');
    });

    this.socket.addEventListener('message', (event: MessageEvent<string>) => {
      this.messagesSubject.next(event.data);
    });

    this.socket.addEventListener('close', () => {
      this.connectionStatus.set('disconnected');
    });

    this.socket.addEventListener('error', () => {
      this.connectionStatus.set('disconnected');
    });
  }

  send(question: string): void {
    this.socket.send(question);
  }
}
