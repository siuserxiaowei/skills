import { App } from 'antd';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ProviderConfig, ProviderKey } from '@/types';
import { ProviderDetail } from '../ProviderDetail';

const mocks = vi.hoisted(() => ({
  toggleProvider: vi.fn(),
  updateProvider: vi.fn(),
  updateProviderKey: vi.fn(),
  deleteProvider: vi.fn(),
  addProviderKey: vi.fn(),
  deleteProviderKey: vi.fn(),
  toggleProviderKey: vi.fn(),
  validateProviderKey: vi.fn(),
  toggleModel: vi.fn(),
  updateModelParams: vi.fn(),
  fetchRemoteModels: vi.fn(),
  saveModels: vi.fn(),
  setSelectedProviderId: vi.fn(),
  invoke: vi.fn(),
  testModel: vi.fn(),
}));

function createProviderFixture(): ProviderConfig {
  return {
    id: 'provider-1',
    name: 'OpenAI',
    provider_type: 'openai',
    api_host: 'https://api.openai.com',
    api_path: '/v1/chat/completions',
    enabled: true,
    custom_headers: null,
    icon: null,
    builtin_id: null,
    models: [
      {
        provider_id: 'provider-1',
        model_id: 'gpt-5.4',
        name: 'GPT 5.4',
        group_name: 'gpt-5.4',
        model_type: 'Chat',
        capabilities: ['TextChat'],
        max_tokens: null,
        enabled: true,
        param_overrides: null,
      },
    ],
    keys: [],
    proxy_config: null,
    sort_order: 0,
    created_at: 0,
    updated_at: 0,
  };
}

function createProviderKeyFixture(overrides: Partial<ProviderKey> = {}): ProviderKey {
  return {
    id: 'key-1',
    provider_id: 'provider-1',
    key_encrypted: 'enc-1',
    key_prefix: 'sk-old',
    enabled: true,
    last_validated_at: null,
    last_error: null,
    rotation_index: 0,
    created_at: 0,
    ...overrides,
  };
}

let provider: ProviderConfig = createProviderFixture();

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback ?? key,
  }),
}));

vi.mock('@lobehub/icons', () => ({
  ProviderIcon: () => <div>provider-icon</div>,
  ModelIcon: () => <div>model-icon</div>,
}));

vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({ count, getItemKey }: { count: number; getItemKey?: (index: number) => string }) => ({
    getVirtualItems: () =>
      Array.from({ length: count }, (_, index) => ({
        index,
        key: getItemKey ? getItemKey(index) : index,
        start: index * 48,
      })),
    getTotalSize: () => count * 48,
    measure: () => {},
    measureElement: () => {},
  }),
}));

vi.mock('../IconPickerModal', () => ({
  default: () => null,
}));

vi.mock('@/components/shared/IconEditor', () => ({
  IconEditor: () => <div>icon-editor</div>,
}));

vi.mock('@/components/shared/DynamicLobeIcon', () => ({
  DynamicLobeIcon: () => <div>dynamic-lobe-icon</div>,
}));

vi.mock('@/components/common/ModelParamSliders', () => ({
  ModelParamSliders: () => <div>model-param-sliders</div>,
}));

vi.mock('@/components/common/CopyButton', () => ({
  CopyButton: () => <button type="button">copy-button</button>,
}));

vi.mock('@/lib/providerIcons', () => ({
  SmartProviderIcon: () => <div>smart-provider-icon</div>,
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: mocks.invoke,
}));

vi.mock('@/stores', () => ({
  useProviderStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      providers: [provider],
      toggleProvider: mocks.toggleProvider,
      updateProvider: mocks.updateProvider,
      updateProviderKey: mocks.updateProviderKey,
      deleteProvider: mocks.deleteProvider,
      addProviderKey: mocks.addProviderKey,
      deleteProviderKey: mocks.deleteProviderKey,
      toggleProviderKey: mocks.toggleProviderKey,
      validateProviderKey: mocks.validateProviderKey,
      toggleModel: mocks.toggleModel,
      updateModelParams: mocks.updateModelParams,
      fetchRemoteModels: mocks.fetchRemoteModels,
      saveModels: mocks.saveModels,
      testModel: mocks.testModel,
    }),
  useUIStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      setSelectedProviderId: mocks.setSelectedProviderId,
    }),
}));

describe('ProviderDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    provider = createProviderFixture();
    mocks.saveModels.mockResolvedValue(undefined);
    mocks.fetchRemoteModels.mockResolvedValue([]);
    mocks.updateProviderKey.mockResolvedValue(undefined);
    mocks.invoke.mockResolvedValue('sk-test-secret');

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it('adds a model from the card-level action and derives the default group from the model id', async () => {
    render(
      <App>
        <ProviderDetail providerId="provider-1" />
      </App>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'settings.addModel' }));

    const dialog = await screen.findByRole('dialog');
    const inputs = within(dialog).getAllByRole('textbox');
    await userEvent.type(inputs[0], 'gpt-5.4-think');
    await userEvent.clear(inputs[1]);
    await userEvent.type(inputs[1], 'GPT 5.4 Think');

    await userEvent.click(within(dialog).getByRole('button', { name: 'settings.addModel' }));

    expect(mocks.saveModels).toHaveBeenCalledWith(
      'provider-1',
      expect.arrayContaining([
        expect.objectContaining({
          model_id: 'gpt-5.4-think',
          name: 'GPT 5.4 Think',
          group_name: 'gpt-5.4',
          model_type: 'Chat',
        }),
      ]),
    );
  });

  it('prefills the current group when adding a model from a group header', async () => {
    render(
      <App>
        <ProviderDetail providerId="provider-1" />
      </App>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'settings.addModelToGroup' }));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByDisplayValue('gpt-5.4')).toBeInTheDocument();
  });

  it('toggles the decrypted key inline between revealed and hidden states', async () => {
    provider.keys = [createProviderKeyFixture()];

    render(
      <App>
        <ProviderDetail providerId="provider-1" />
      </App>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'settings.viewKey' }));

    await waitFor(() => {
      expect(mocks.invoke).toHaveBeenCalledWith('get_decrypted_provider_key', { keyId: 'key-1' });
    });

    expect(screen.getByText('sk-test-secret')).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: 'settings.viewKey' })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'common.hide' }));

    expect(screen.queryByText('sk-test-secret')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'settings.viewKey' })).toBeInTheDocument();
    expect(mocks.invoke).toHaveBeenCalledTimes(1);
  });

  it('uses plain text input when adding a key', async () => {
    render(
      <App>
        <ProviderDetail providerId="provider-1" />
      </App>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'settings.addKey' }));

    const dialog = await screen.findByRole('dialog');
    const input = within(dialog).getByRole('textbox');
    await userEvent.type(input, 'sk-added-secret');
    await userEvent.click(within(dialog).getByRole('button', { name: 'common.confirm' }));

    await waitFor(() => {
      expect(mocks.addProviderKey).toHaveBeenCalledWith('provider-1', 'sk-added-secret');
    });
  });

  it('uses plain text input when editing a key and saves the updated value', async () => {
    provider.keys = [createProviderKeyFixture()];

    render(
      <App>
        <ProviderDetail providerId="provider-1" />
      </App>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'settings.editKey' }));

    await waitFor(() => {
      expect(mocks.invoke).toHaveBeenCalledWith('get_decrypted_provider_key', { keyId: 'key-1' });
    });

    const dialog = await screen.findByRole('dialog');
    const input = within(dialog).getByRole('textbox');
    expect(input).toHaveValue('sk-test-secret');
    await userEvent.clear(input);
    await userEvent.type(input, 'sk-updated-secret');

    await userEvent.click(within(dialog).getByRole('button', { name: 'settings.saveKey' }));

    await waitFor(() => {
      expect(mocks.updateProviderKey).toHaveBeenCalledWith('key-1', 'sk-updated-secret');
    });
  });

  it('syncs remote models without overwriting existing local model settings', async () => {
    provider.models = [
      {
        provider_id: 'provider-1',
        model_id: 'gpt-5.4',
        name: 'Local GPT 5.4',
        group_name: 'local-group',
        model_type: 'Chat',
        capabilities: ['TextChat', 'Reasoning'],
        max_tokens: 16000,
        enabled: false,
        param_overrides: { temperature: 0.1, top_p: 0.8 },
      },
      {
        provider_id: 'provider-1',
        model_id: 'legacy-model',
        name: 'Legacy Model',
        group_name: 'legacy',
        model_type: 'Chat',
        capabilities: ['TextChat'],
        max_tokens: 4000,
        enabled: true,
        param_overrides: null,
      },
    ];

    mocks.fetchRemoteModels.mockResolvedValue([
      {
        provider_id: 'provider-1',
        model_id: 'gpt-5.4',
        name: 'Remote GPT 5.4',
        group_name: 'remote-group',
        model_type: 'Chat',
        capabilities: ['TextChat'],
        max_tokens: 32000,
        enabled: true,
        param_overrides: null,
      },
      {
        provider_id: 'provider-1',
        model_id: 'gpt-5.4-mini',
        name: 'Remote GPT 5.4 Mini',
        group_name: 'remote-group',
        model_type: 'Chat',
        capabilities: ['TextChat'],
        max_tokens: 8000,
        enabled: true,
        param_overrides: null,
      },
    ]);

    render(
      <App>
        <ProviderDetail providerId="provider-1" />
      </App>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'settings.syncModels' }));

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByRole('checkbox', { name: 'gpt-5.4' })).toBeChecked();
    expect(within(dialog).getByRole('checkbox', { name: 'legacy-model' })).toBeChecked();
    expect(within(dialog).getByRole('checkbox', { name: 'gpt-5.4-mini' })).not.toBeChecked();
    expect(within(dialog).getByText('settings.remoteMissing')).toBeInTheDocument();

    await userEvent.click(within(dialog).getByRole('checkbox', { name: 'gpt-5.4-mini' }));
    await userEvent.click(within(dialog).getByRole('button', { name: 'settings.applyModelSync' }));

    await waitFor(() => {
      expect(mocks.saveModels).toHaveBeenCalledWith(
        'provider-1',
        expect.arrayContaining([
          expect.objectContaining({
            model_id: 'gpt-5.4',
            name: 'Local GPT 5.4',
            group_name: 'local-group',
            enabled: false,
            param_overrides: { temperature: 0.1, top_p: 0.8 },
          }),
          expect.objectContaining({
            model_id: 'legacy-model',
            name: 'Legacy Model',
            group_name: 'legacy',
          }),
          expect.objectContaining({
            model_id: 'gpt-5.4-mini',
            name: 'Remote GPT 5.4 Mini',
            group_name: 'remote-group',
          }),
        ]),
      );
    });
  });
});
