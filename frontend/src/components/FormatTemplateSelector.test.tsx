import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FormatTemplateSelector from './FormatTemplateSelector';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockTemplates = [
  { id: 1, name: '标准论文', is_default: true, created_at: '2026-01-01T00:00:00Z' },
  { id: 2, name: '实验报告', is_default: false, created_at: '2026-01-02T00:00:00Z' },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe('FormatTemplateSelector', () => {
  it('renders the label', () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
    render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />);
    expect(screen.getByText('格式模板')).toBeDefined();
  });

  it('renders select and upload button', () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
    render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />);
    expect(screen.getByRole('combobox')).toBeDefined();
    expect(screen.getByText('上传模板')).toBeDefined();
  });

  it('fetches templates on mount and selects default', async () => {
    const onSelect = vi.fn();
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockTemplates });

    render(<FormatTemplateSelector selectedId={null} onSelect={onSelect} />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/format-templates');
    });

    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith(1);
    });
  });

  it('shows templates in the select dropdown', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockTemplates });

    render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('标准论文 (默认)')).toBeDefined();
      expect(screen.getByText('实验报告')).toBeDefined();
    });
  });

  it('does not auto-select when selectedId is already set', async () => {
    const onSelect = vi.fn();
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockTemplates });

    render(<FormatTemplateSelector selectedId={2} onSelect={onSelect} />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalled();
    });

    expect(onSelect).not.toHaveBeenCalled();
  });

  it('shows upload section when upload button is clicked', () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });
    render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />);

    fireEvent.click(screen.getByText('上传模板'));
    expect(screen.getByPlaceholderText('模板名称')).toBeDefined();
  });

  it('uploads a template successfully', async () => {
    const newTemplate = { id: 3, name: '新模板', is_default: false, created_at: '2026-07-07T00:00:00Z' };
    const onSelect = vi.fn();

    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockTemplates });
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: newTemplate });

    render(<FormatTemplateSelector selectedId={null} onSelect={onSelect} />);

    await waitFor(() => expect(api.get).toHaveBeenCalled());

    // Click upload button to show the form
    fireEvent.click(screen.getByText('上传模板'));

    // Fill in name and file
    const nameInput = screen.getByPlaceholderText('模板名称');
    fireEvent.change(nameInput, { target: { value: '新模板' } });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeNull();
    const file = new File(['dummy'], 'template.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    // Click submit
    fireEvent.click(screen.getByText('上传并解析'));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/format-templates/upload', expect.any(FormData));
    });

    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith(3);
    });
  });

  it('shows error message when upload fails', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockTemplates });
    (api.post as ReturnType<typeof vi.fn>).mockRejectedValue({
      response: { data: { detail: '文件格式不支持' } },
    });

    render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />);

    await waitFor(() => expect(api.get).toHaveBeenCalled());

    fireEvent.click(screen.getByText('上传模板'));

    const nameInput = screen.getByPlaceholderText('模板名称');
    fireEvent.change(nameInput, { target: { value: '新模板' } });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['dummy'], 'template.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByText('上传并解析'));

    await waitFor(() => {
      expect(screen.getByText('文件格式不支持')).toBeDefined();
    });
  });

  it('disables upload button when uploading', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockTemplates });
    (api.post as ReturnType<typeof vi.fn>).mockImplementation(() => new Promise(() => {}));

    render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />);

    await waitFor(() => expect(api.get).toHaveBeenCalled());

    fireEvent.click(screen.getByText('上传模板'));

    const nameInput = screen.getByPlaceholderText('模板名称');
    fireEvent.change(nameInput, { target: { value: '新模板' } });

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['dummy'], 'template.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByText('上传并解析'));

    await waitFor(() => {
      expect(screen.getByText('解析中...')).toBeDefined();
    });
  });

  it('handles API fetch error gracefully', () => {
    (api.get as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'));
    expect(() => render(<FormatTemplateSelector selectedId={null} onSelect={vi.fn()} />)).not.toThrow();
  });
});
