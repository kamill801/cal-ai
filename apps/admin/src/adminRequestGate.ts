export class AdminRequestGate {
  private blocked = false;
  private controllers = new Set<AbortController>();

  get denied() { return this.blocked; }

  open(): AbortController {
    const controller = new AbortController();
    if (this.blocked) controller.abort();
    else this.controllers.add(controller);
    return controller;
  }

  accepts(controller: AbortController): boolean {
    return !this.blocked && !controller.signal.aborted;
  }

  release(controller: AbortController): void {
    controller.abort();
    this.controllers.delete(controller);
  }

  revoke(): void {
    this.blocked = true;
    this.controllers.forEach((controller) => controller.abort());
    this.controllers.clear();
  }
}
