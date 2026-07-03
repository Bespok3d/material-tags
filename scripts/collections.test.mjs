// Unit tests for the collection (kind:collection) path through this co-repo's publishing tooling:
// generate-atom.mjs (a collection atom) and assemble-list.mjs (partitioning atoms into a sibling
// collections[]). Run with: node --test scripts/collections.test.mjs

import { test } from 'node:test'
import assert from 'node:assert/strict'

import { buildCollectionAtom, buildAtom } from './generate-atom.mjs'
import { assemble } from './assemble-list.mjs'

const COLLECTION_MANIFEST = {
  kind: 'collection',
  name: 'all-the-tags',
  title: 'All the Tags',
  version: '0.1.0',
  description: 'The whole RFID tag stack.',
  tagline: 'Every spool, identified.',
  category: 'filament',
  channel: 'experiment',
  publisher: 'PLACEHOLDER',
  printer_specific: false,
  published_at: '2026-06-30',
  updated_at: '2026-06-30',
  changelog: 'doc/CHANGELOG.md',
  members: [{ id: 'rfid-ntag', version: '>=0.1.6' }],
}

const PLUGIN_MANIFEST = {
  name: 'rfid-opentag',
  title: 'OpenTag',
  version: '0.1.0',
  description: 'OpenTag decoder.',
  tagline: 'OpenTag.',
  category: 'filament',
  channel: 'experiment',
  publisher: 'PLACEHOLDER',
  printer_specific: false,
  published_at: '2026-06-30',
  updated_at: '2026-06-29',
  provides: [{ service: 'opentag' }],
  require: [{ service: 'rfid-service' }],
  conflicts: [],
}

test('buildCollectionAtom carries kind + members + doc_url, never a download_url', () => {
  const atom = buildCollectionAtom(COLLECTION_MANIFEST, 'https://example/doc')
  assert.equal(atom.kind, 'collection')
  assert.deepEqual(atom.members, [{ id: 'rfid-ntag', version: '>=0.1.6' }])
  assert.equal(atom.doc_url, 'https://example/doc')
  assert.equal(atom.download_url, undefined)
  assert.equal(atom.changelog_url, 'all-the-tags/doc/CHANGELOG.md')
})

test('assemble partitions collection atoms into collections[] and strips the kind discriminator', () => {
  const pluginAtom = buildAtom(PLUGIN_MANIFEST, 'rfid-opentag-0.1.0.b3', 'doc')
  const collectionAtom = buildCollectionAtom(COLLECTION_MANIFEST, 'doc')
  const index = assemble([pluginAtom, collectionAtom])
  assert.deepEqual(index.plugins.map((plugin) => plugin.name), ['rfid-opentag'])
  assert.equal(index.collections.length, 1)
  assert.equal(index.collections[0].name, 'all-the-tags')
  assert.equal(index.collections[0].kind, undefined)
  assert.deepEqual(index.collections[0].members, [{ id: 'rfid-ntag', version: '>=0.1.6' }])
  assert.equal(index.updated, '2026-06-30')
})

test('assemble always emits a collections[] slot, even with no collections', () => {
  assert.deepEqual(assemble([]).collections, [])
})
