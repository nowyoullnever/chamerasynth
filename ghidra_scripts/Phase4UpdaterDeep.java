// Offline Phase 4 updater evidence export.  Seed/function boundaries remain
// Ghidra analysis hypotheses; this script never changes the source firmware.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

public class Phase4UpdaterDeep extends GhidraScript {
    private static final long FILE_BIAS = 0x200;
    private static final long[] SEEDS = {
        0x00021170L, 0x000215b4L, 0x00001b20L, 0x00001180L, 0x00001174L,
        0x0003060cL, 0x00001aecL, 0x0000119cL, 0x000004ccL, 0x000257b8L,
        0x00030028L, 0x0003028cL, 0x00030400L, 0x00030aecL, 0x00030b14L,
        0x000306b4L, 0x00030800L, 0x000303a4L, 0x00030a8cL, 0x00030424L
    };
    private static String hx(Address a) { return String.format("0x%08x", a.getOffset()); }
    private static String fo(Address a) { return String.format("0x%06x", a.getOffset() + FILE_BIAS); }
    private static String q(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""; }
    private static String hex(byte[] b) { StringBuilder s = new StringBuilder(); for (byte x : b) s.append(String.format("%02x", x & 0xff)); return s.toString(); }
    private Function get(long va) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
        new DisassembleCommand(a, null, true).applyTo(currentProgram, monitor);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f == null) new CreateFunctionCmd("phase4_seed_" + Long.toHexString(va), a, null, SourceType.ANALYSIS).applyTo(currentProgram, monitor);
        return currentProgram.getFunctionManager().getFunctionAt(a);
    }
    private void array(PrintWriter p, List<String> xs) { p.print("["); for (int i=0;i<xs.size();i++) { if(i>0)p.print(","); p.print(q(xs.get(i))); } p.print("]"); }
    @Override public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("expected output directory");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        File pseudo = new File(root, "pseudocode"); pseudo.mkdirs();
        DecompInterface d = new DecompInterface(); d.setSimplificationStyle("decompile"); d.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(root, "updater_deep.json")))) {
            out.println("{\"mapping\":\"file_offset = va + 0x200; hypothesis only\",\"functions\":[");
            boolean first = true;
            for (long va : SEEDS) {
                Function f = get(va); Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
                if (!first) out.println(","); first = false;
                out.print("{\"seed_va\":" + q(hx(a)) + ",\"seed_file_offset\":" + q(fo(a)));
                if (f == null) { out.print(",\"status\":\"no_function_at_seed\"}"); continue; }
                byte[] b = new byte[Math.min(64, (int)f.getBody().getNumAddresses())]; currentProgram.getMemory().getBytes(f.getEntryPoint(), b);
                out.print(",\"entry_va\":" + q(hx(f.getEntryPoint())) + ",\"entry_file_offset\":" + q(fo(f.getEntryPoint())) + ",\"body_min_va\":" + q(hx(f.getBody().getMinAddress())) + ",\"body_max_va\":" + q(hx(f.getBody().getMaxAddress())) + ",\"head_hex\":" + q(hex(b)));
                List<String> callers = new ArrayList<>(); for (Function x : f.getCallingFunctions(monitor)) callers.add(hx(x.getEntryPoint())); out.print(",\"calling_functions\":"); array(out, callers);
                List<String> refs = new ArrayList<>(); for (Reference r : currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint())) refs.add(hx(r.getFromAddress()) + "->" + hx(r.getToAddress())); out.print(",\"incoming_references\":"); array(out, refs);
                List<String> calls = new ArrayList<>(); List<String> instructions = new ArrayList<>(); InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (it.hasNext()) { Instruction i = it.next(); if (instructions.size() < 80) instructions.add(hx(i.getAddress()) + " " + i.toString()); if (i.getFlowType().isCall()) for (Address to : i.getFlows()) calls.add(hx(i.getAddress()) + "->" + hx(to)); }
                out.print(",\"direct_call_edges\":"); array(out, calls); out.print(",\"instructions\":"); array(out, instructions);
                DecompileResults result = d.decompileFunction(f, 90, monitor); String n = String.format("%06x.c", f.getEntryPoint().getOffset()+FILE_BIAS);
                try (PrintWriter c = new PrintWriter(new FileWriter(new File(pseudo, n)))) { c.println("/* seed " + hx(a) + ", entry " + hx(f.getEntryPoint()) + ", file " + fo(f.getEntryPoint()) + " */"); c.println(result.getDecompiledFunction()==null ? "/* no pseudocode */" : result.getDecompiledFunction().getC()); }
                out.print(",\"decompile_status\":" + q(result.decompileCompleted() ? "complete" : "incomplete") + ",\"pseudocode_file\":" + q("pseudocode/"+n) + "}");
            }
            out.println("],\"limitations\":[\"Ghidra function boundaries/types are static-analysis hypotheses.\",\"No flash command was executed.\"]}");
        } finally { d.dispose(); }
    }
}
