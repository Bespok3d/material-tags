// Assemble this co-repo's own published sub-list (index.json at the repo root) from the per-plugin
// atoms in dist/. The output is the ADR-0012 federated-index shape, identical to what main-index
// emits, so the app loads it through the same resolver. main-index references this file by URL in
// its lists[], so the official catalog picks these plugins up without copying their atoms.
// Signing (index.json.sig) is deferred.

import { readdir, readFile, writeFile } from 'node:fs/promises'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const LIST_NAME = 'Material Tags'
const LIST_PUBLISHER = 'PLACEHOLDER'

function serviceName(provided) {
  return typeof provided === 'string' ? provided : provided.service
}

function requiredServices(atom) {
  return (atom.require ?? []).map((requirement) => requirement.service)
}

function providerByService(atoms) {
  const providers = {}
  atoms.forEach((atom) => {
    ;(atom.provides ?? []).forEach((provided) => {
      const service = serviceName(provided)
      if (!(service in providers)) providers[service] = atom.name
    })
  })
  return providers
}

function resolveDeps(atom, providers) {
  const resolved = []
  requiredServices(atom).forEach((service) => {
    const providerId = providers[service] ?? service
    if (!resolved.includes(providerId)) resolved.push(providerId)
  })
  return resolved
}

function isCollectionAtom(atom) {
  return atom.kind === 'collection'
}

// A collection atom carries `kind` only so the assembler can route it; strip it from the published
// entry (a collection's type is the collections[] array it sits in, just as a plugin entry carries
// no `kind:plugin`). Collections have no `require`/`deps`; their members[] passes through verbatim.
function toCollectionEntry(atom) {
  const { kind: _kind, ...entry } = atom
  return entry
}

// Drop the internal `require` (only the assembler needs it) and replace it with the resolved `deps`,
// so each published entry matches the catalog entry shape the app expects. This is a leaf list
// (lists: []); main-index is the list-of-lists that references it. Collection atoms are partitioned
// into a sibling collections[] (install-orchestration metadata, never resolved to a .b3).
export function assemble(atoms) {
  const sorted = [...atoms].sort((earlier, later) => earlier.name.localeCompare(later.name))
  const pluginAtoms = sorted.filter((atom) => !isCollectionAtom(atom))
  const collectionAtoms = sorted.filter(isCollectionAtom)
  const providers = providerByService(pluginAtoms)
  const plugins = pluginAtoms.map((atom) => {
    const { require: _require, ...entry } = atom
    return { ...entry, deps: resolveDeps(atom, providers) }
  })
  const collections = collectionAtoms.map(toCollectionEntry)
  const updated = [...plugins, ...collections].reduce((latest, entry) => (entry.updated_at > latest ? entry.updated_at : latest), '')
  return { schema_version: 1, name: LIST_NAME, publisher: LIST_PUBLISHER, updated, plugins, collections, lists: [] }
}

async function main() {
  const scriptDir = dirname(fileURLToPath(import.meta.url))
  const repoDir = dirname(scriptDir)
  const distDir = join(repoDir, 'dist')
  const names = (await readdir(distDir).catch(() => [])).filter((name) => name.endsWith('.atom.json'))
  const atoms = await Promise.all(names.map((name) => readFile(join(distDir, name), 'utf8').then(JSON.parse)))
  const index = assemble(atoms)
  await writeFile(join(repoDir, 'index.json'), `${JSON.stringify(index, null, 2)}\n`)
  process.stdout.write(`Wrote index.json (${index.plugins.length} plugins, ${index.collections.length} collections)\n`)
}

if (process.argv[1] && process.argv[1].endsWith('assemble-list.mjs')) {
  main().catch((error) => {
    process.stderr.write(`assemble-list failed: ${error.message}\n`)
    process.exit(1)
  })
}
