import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { getProjectMapPath, getWorkspaceRoot } from '../utils/workspace';
import { log } from '../utils/output';

interface Entity {
  id?: string;
  name: string;
  type: string;
  file_path: string;
  line_start: number;
  line_end?: number;
  language?: string;
  docstring?: string;
  summary?: string;
}

interface ProjectMapFile {
  path: string;
  language: string;
  size_bytes: number;
  framework_hints?: string[];
}

interface ProjectMap {
  root: string;
  entities: Entity[];
  files: ProjectMapFile[];
}

const TYPE_ICONS: Record<string, string> = {
  class: 'symbol-class',
  function: 'symbol-function',
  method: 'symbol-method',
  module: 'symbol-namespace',
  api: 'symbol-interface',
  route: 'symbol-event',
  workflow: 'symbol-misc',
  file: 'symbol-file',
  service: 'symbol-property',
};

class SymbolTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    public entity?: Entity,
    public filePath?: string,
    public isFile?: boolean,
    public fileEntityCount?: number,
  ) {
    super(label, collapsibleState);

    if (entity && filePath) {
      this.tooltip = entity.docstring || `${entity.type} ${entity.name} at ${path.basename(filePath)}:${entity.line_start}`;
      this.description = `${entity.type} · L${entity.line_start}`;
      this.iconPath = new vscode.ThemeIcon(TYPE_ICONS[entity.type] || 'symbol-misc');

      const absolutePath = filePath.startsWith('/')
        ? filePath
        : path.join(getWorkspaceRoot() || '', filePath);
      this.command = {
        command: 'vscode.open',
        title: 'Open File',
        arguments: [
          vscode.Uri.file(absolutePath),
          {
            selection: new vscode.Range(
              new vscode.Position(Math.max(0, entity.line_start - 1), 0),
              new vscode.Position(Math.max(0, entity.line_start - 1), 0),
            ),
          },
        ],
      };
    } else if (isFile && filePath) {
      this.iconPath = vscode.ThemeIcon.File;
      this.resourceUri = vscode.Uri.file(
        path.join(getWorkspaceRoot() || '', filePath),
      );
      if (typeof fileEntityCount === 'number') {
        this.description = fileEntityCount > 0 ? `${fileEntityCount} symbols` : '';
      }
    }
  }
}

export class SymbolExplorerProvider implements vscode.TreeDataProvider<SymbolTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<SymbolTreeItem | undefined | null | void> =
    new vscode.EventEmitter<SymbolTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<SymbolTreeItem | undefined | null | void> =
    this._onDidChangeTreeData.event;

  private projectMap: ProjectMap | null = null;
  private workspaceRoot: string | null = null;
  private entitiesByFile: Map<string, Entity[]> = new Map();

  constructor() {
    this.workspaceRoot = getWorkspaceRoot();
    this.loadProjectMap();
  }

  private loadProjectMap(): void {
    const projectMapPath = getProjectMapPath();
    if (!projectMapPath || !fs.existsSync(projectMapPath)) {
      return;
    }

    try {
      const content = fs.readFileSync(projectMapPath, 'utf-8');
      this.projectMap = JSON.parse(content);
      this.indexEntities();
      log(`Loaded project map with ${this.projectMap?.entities.length || 0} entities`);
    } catch (error) {
      log(`Failed to load project map: ${error}`);
    }
  }

  private indexEntities(): void {
    this.entitiesByFile.clear();
    if (!this.projectMap) {
      return;
    }
    for (const entity of this.projectMap.entities) {
      const filePath = (entity as any).file_path || (entity as any).file;
      if (!filePath) continue;
      if (!this.entitiesByFile.has(filePath)) {
        this.entitiesByFile.set(filePath, []);
      }
      this.entitiesByFile.get(filePath)!.push({ ...entity, file_path: filePath });
    }
    log(`Indexed entities for ${this.entitiesByFile.size} files`);
  }

  getTreeItem(element: SymbolTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: SymbolTreeItem): Thenable<SymbolTreeItem[]> {
    if (!this.projectMap) {
      this.loadProjectMap();
      if (!this.projectMap) {
        return Promise.resolve([
          new SymbolTreeItem(
            'No project map found. Run "Build Index" first.',
            vscode.TreeItemCollapsibleState.None,
          ),
        ]);
      }
    }

    if (!element) {
      // Root level: show only files that have entities, sorted with entity-rich files first
      const files = (this.projectMap?.files || [])
        .map((file) => ({
          file,
          count: this.entitiesByFile.get(file.path)?.length || 0,
        }))
        .filter((f) => f.count > 0)
        .sort((a, b) => {
          if (a.count !== b.count) return b.count - a.count;
          return a.file.path.localeCompare(b.file.path);
        });

      if (files.length === 0) {
        return Promise.resolve([
          new SymbolTreeItem(
            'No symbols found. Run "Build Index" to scan code.',
            vscode.TreeItemCollapsibleState.None,
          ),
        ]);
      }

      const items = files.map(
        ({ file, count }) =>
          new SymbolTreeItem(
            file.path,
            vscode.TreeItemCollapsibleState.Collapsed,
            undefined,
            file.path,
            true,
            count,
          ),
      );
      return Promise.resolve(items);
    }

    // Show entities in this file
    if (element.isFile && element.filePath) {
      const filePath = element.filePath;
      const entities = this.entitiesByFile.get(filePath) || [];
      const sorted = [...entities].sort((a, b) => a.line_start - b.line_start);

      const items = sorted.map(
        (entity) =>
          new SymbolTreeItem(
            entity.name,
            vscode.TreeItemCollapsibleState.None,
            entity,
            filePath,
          ),
      );

      if (items.length === 0) {
        return Promise.resolve([
          new SymbolTreeItem(
            `(no symbols in ${path.basename(filePath)})`,
            vscode.TreeItemCollapsibleState.None,
          ),
        ]);
      }

      return Promise.resolve(items);
    }

    return Promise.resolve([]);
  }

  async refresh(): Promise<void> {
    this.loadProjectMap();
    this._onDidChangeTreeData.fire();
  }
}
