import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-message-input',
  imports: [FormsModule],
  templateUrl: './message-input.html',
  styleUrl: './message-input.scss',
})
export class MessageInput {
  readonly disabled = input<boolean>(false);
  readonly send = output<string>();

  questionText = '';

  submit(): void {
    const trimmed = this.questionText.trim();
    if (!trimmed || this.disabled()) {
      return;
    }
    this.send.emit(trimmed);
    this.questionText = '';
  }
}
