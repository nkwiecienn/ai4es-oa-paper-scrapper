import { useEffect, useState } from 'react';
import {
  TextField,
  Box,
  Stack,
  Typography,
  Alert,
} from '@mui/material';

const DOI_REGEX = /^10\.\d{4,9}\/[-._;()/:A-Z0-9]+$/i;
const ARXIV_REGEX = /^(?:arxiv:)?(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?\/\d{7}(?:v\d+)?)$/i;
const PUBMED_REGEX = /^(?:pmid:)?\d+$/i;
const SPLIT_REGEX = /[;,\n\t]+|\s{2,}/;

const normalizeInput = (input) =>
  input
    .replace(/\r\n?/g, '\n')
    .replace(/\u00A0/g, ' ')
    .trim();

const splitIdentifiers = (input) => {
  const normalized = normalizeInput(input);

  if (!normalized) {
    return [];
  }

  return normalized
    .split(SPLIT_REGEX)
    .map((value) => value.trim())
    .filter(Boolean);
};

const classifyIdentifier = (identifier) => {
  if (DOI_REGEX.test(identifier)) {
    return 'DOI';
  }

  if (ARXIV_REGEX.test(identifier)) {
    return 'arXiv';
  }

  if (PUBMED_REGEX.test(identifier)) {
    return 'PubMed';
  }

  return null;
};

const parseIdentifiers = (input) => {
  const items = splitIdentifiers(input);

  return items.map((value, index) => ({
    index,
    value,
    type: classifyIdentifier(value),
  }));
};

const secondaryActionClassName =
  'inline-flex items-center justify-center rounded border border-white/15 bg-background/20 px-5 py-3 text-sm font-semibold text-on-surface transition-transform duration-200 hover:-translate-y-0.5 hover:border-white/25 hover:bg-background/30 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-surface_container disabled:pointer-events-none disabled:opacity-60';

export const PaperIdentifierInput = ({
  onIdentifiersChange,
  onDoisChange,
  initialValue = '',
}) => {
  const [text, setText] = useState(initialValue);
  const [status, setStatus] = useState({
    type: 'empty',
    validCount: 0,
    totalCount: 0,
    messages: [],
    fileName: '',
  });

  useEffect(() => {
    setText(initialValue);
    processInput(initialValue);
  }, [initialValue]);

  const emitIdentifiers = (items) => {
    if (onIdentifiersChange) {
      onIdentifiersChange(items);
    }

    if (onDoisChange) {
      onDoisChange(items.map((item) => item.value));
    }
  };

  const processInput = (input, fileName = '') => {
    const parsed = parseIdentifiers(input);

    if (!parsed.length) {
      setStatus({
        type: 'empty',
        validCount: 0,
        totalCount: 0,
        messages: [],
        fileName,
      });
      emitIdentifiers([]);
      return;
    }

    const validItems = parsed.filter((item) => item.type);
    const invalidItems = parsed.filter((item) => !item.type);

    emitIdentifiers(validItems);

    if (invalidItems.length) {
      setStatus({
        type: validItems.length ? 'partial' : 'error',
        validCount: validItems.length,
        totalCount: parsed.length,
        fileName,
        messages: invalidItems.map(
          (item) => `Item ${item.index + 1} is not a DOI, arXiv ID, or PubMed ID: "${item.value}"`
        ),
      });
      return;
    }

    setStatus({
      type: 'success',
      validCount: validItems.length,
      totalCount: parsed.length,
      fileName,
      messages: [],
    });
  };

  const handleTextChange = (event) => {
    const value = event.target.value;
    setText(value);
    processInput(value);
  };

  const handleFileChange = async (event) => {
    if (!event.target.files?.length) {
      return;
    }

    const file = event.target.files[0];

    try {
      const fileText = await file.text();
      setText(fileText);
      processInput(fileText, file.name);
    } catch (_) {
      setStatus({
        type: 'error',
        validCount: 0,
        totalCount: 0,
        fileName: file.name,
        messages: ['Failed to read the selected file.'],
      });
      emitIdentifiers([]);
    } finally {
      event.target.value = '';
    }
  };

  const helperText = 'Paste one identifier or a list separated by commas, semicolons, tabs, or new lines. You can also upload a .txt file.';
  const messageColor = status.type === 'error' ? 'error.main' : status.type === 'partial' ? 'warning.main' : 'success.main';

  return (
    <Stack spacing={2.5} sx={{ width: '100%', textAlign: 'left' }}>
      <Box>
        <Typography variant="h6" sx={{ color: 'var(--color-text)', fontWeight: 700 }}>
          Enter paper identifiers
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 1.5,
          justifyContent: 'space-between',
        }}
      >
        <label className={`${secondaryActionClassName} cursor-pointer`}>
          Upload .txt file
          <input
            type="file"
            accept=".txt,text/plain"
            onChange={handleFileChange}
            hidden
          />
        </label>

        <Typography variant="body2" sx={{ color: 'var(--color-text-muted)' }}>
          {status.fileName ? `Selected file: ${status.fileName}` : 'No file selected'}
        </Typography>
      </Box>

      <TextField
        label="Identifiers"
        placeholder="10.1000/xyz123, arXiv:2401.01234, PMID: 12345678"
        multiline
        minRows={4}
        maxRows={8}
        value={text}
        onChange={handleTextChange}
        fullWidth
        variant="outlined"
        helperText={helperText}
        InputLabelProps={{
          sx: {
            color: 'var(--color-text-muted)',
            '&.Mui-focused': {
              color: 'var(--color-text)',
            },
          },
        }}
        FormHelperTextProps={{
          sx: {
            color: 'var(--color-text-muted)',
          },
        }}
        sx={{
          '& .MuiInputBase-root': {
            alignItems: 'flex-start',
            backgroundColor: 'rgba(255, 255, 255, 0.03)',
            color: 'var(--color-text)',
          },
          '& .MuiInputBase-input::placeholder': {
            color: 'var(--color-text-muted)',
            opacity: 1,
          },
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 255, 255, 0.16)',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 255, 255, 0.28)',
          },
          '& .MuiFormHelperText-root': {
            color: 'var(--color-text-muted)',
          },
        }}
      />

      {status.type !== 'empty' && (
        <Alert severity={status.type === 'success' ? 'success' : status.type === 'partial' ? 'warning' : 'error'}>
          {status.type === 'success' && `Accepted ${status.validCount} identifier${status.validCount === 1 ? '' : 's'}.`}
          {status.type === 'partial' && `${status.validCount} of ${status.totalCount} identifiers accepted. Some entries need attention.`}
          {status.type === 'error' && 'No valid identifiers were found.'}
        </Alert>
      )}

      {status.messages.length > 0 && (
        <Alert severity={status.type === 'error' ? 'error' : 'warning'} sx={{ whiteSpace: 'pre-wrap' }}>
          <Stack spacing={0.5}>
            {status.messages.map((message) => (
              <Typography key={message} variant="body2" sx={{ color: messageColor }}>
                {message}
              </Typography>
            ))}
          </Stack>
        </Alert>
      )}
    </Stack>
  );
};

export const DoIInput = PaperIdentifierInput;
