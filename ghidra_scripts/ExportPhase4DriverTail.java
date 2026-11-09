// Focused, read-only Phase 4 evidence export.  All addresses are logical VAs
// under the unverified payload-base-zero hypothesis.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;

public class ExportPhase4DriverTail extends GhidraScript {
    private static final long FILE_BIAS = 0x200;
    private static final long TAIL_START = 0x1aec00;
    private static final long TAIL_END = 0x1ffdff;
    private static final long[] FUNCTION_SEEDS = {
        0x21a2c, 0x985c, 0x1b8dc, 0x1b968, 0x1d380,
        0x63b0, 0x25a38, 0x25984, 0x21dc8, 0x21d20, 0x220cc, 0x6378,
        0x1e234, 0x1310, 0xb438c,
        0x1a248, 0x1aa38, 0x376ec, 0x51d70, 0x52394, 0x5fb5c,
        0x6066c, 0x80f0c, 0xb48d4, 0xdeec0
    };
    private static final long[] STRING_SEEDS = { 0x1e294, 0x1e2a0, 0x1e2c8, 0x21b18, 0xb4500 };

    private static String esc(String s) {
        if (s == null) return "null";
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\"";
    }
    private static String hex(Address a) { return a == null ? null : String.format("0x%08x", a.getOffset()); }
    private static String file(Address a) { return a == null ? null : String.format("0x%06x", a.getOffset() + FILE_BIAS); }
    private Address a(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    private static String hx(byte[] b) { StringBuilder s = new StringBuilder(); for (byte x : b) s.append(String.format("%02x", x & 0xff)); return s.toString(); }
    private void values(PrintWriter o, List<String> v) { o.print("["); for (int i=0;i<v.size();i++) { if(i>0)o.print(","); o.print(esc(v.get(i))); } o.print("]"); }

    private void function(PrintWriter o, Function f, DecompInterface d, File pseudo) throws Exception {
        if (f == null) { o.print("null"); return; }
        byte[] first = new byte[Math.min(32, (int)f.getBody().getNumAddresses())];
        currentProgram.getMemory().getBytes(f.getEntryPoint(), first);
        List<String> callers = new ArrayList<>(), callees = new ArrayList<>(), direct = new ArrayList<>();
        for (Function x : f.getCallingFunctions(monitor)) callers.add(hex(x.getEntryPoint()));
        for (Function x : f.getCalledFunctions(monitor)) callees.add(hex(x.getEntryPoint()));
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        while (it.hasNext()) { Instruction i=it.next(); if(i.getFlowType().isCall()) for(Address to:i.getFlows()) direct.add(hex(i.getAddress())+"->"+hex(to)); }
        DecompileResults result = d.decompileFunction(f, 60, monitor);
        String name = String.format("%06x.c", f.getEntryPoint().getOffset()+FILE_BIAS);
        try(PrintWriter c=new PrintWriter(new FileWriter(new File(pseudo,name)))) { c.println("/* Ghidra inferred pseudocode; file offset="+file(f.getEntryPoint())+" */"); c.println(result.getDecompiledFunction()==null?"/* no pseudocode */":result.getDecompiledFunction().getC()); }
        o.print("{\"entry_va\":"+esc(hex(f.getEntryPoint()))+",\"entry_file_offset\":"+esc(file(f.getEntryPoint()))+",\"body_min_va\":"+esc(hex(f.getBody().getMinAddress()))+",\"body_max_va\":"+esc(hex(f.getBody().getMaxAddress()))+",\"head_hex\":"+esc(hx(first))+",\"callers\":"); values(o,callers); o.print(",\"callees\":"); values(o,callees); o.print(",\"direct_call_edges\":"); values(o,direct); o.print(",\"decompile_complete\":"+(result.decompileCompleted()?"true":"false")+",\"pseudocode_file\":"+esc("pseudocode/"+name)+"}");
    }

    @Override public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("expected output directory");
        File root = new File(getScriptArgs()[0]); root.mkdirs(); File pseudo = new File(root,"pseudocode"); pseudo.mkdirs();
        DecompInterface d = new DecompInterface(); d.setSimplificationStyle("decompile"); d.openProgram(currentProgram);
        try(PrintWriter o=new PrintWriter(new FileWriter(new File(root,"driver_tail_graph.json")))) {
            o.println("{\"mapping\":\"file_offset = logical_va + 0x200; hypothesis only\",");
            o.println("\"function_seeds\":[");
            for(int i=0;i<FUNCTION_SEEDS.length;i++) { if(i>0)o.println(","); Address at=a(FUNCTION_SEEDS[i]); o.print("{\"requested_va\":"+esc(hex(at))+",\"requested_file_offset\":"+esc(file(at))+",\"function\":"); function(o,currentProgram.getFunctionManager().getFunctionContaining(at),d,pseudo); o.print("}"); }
            o.println("],\"string_reference_sites\":[");
            boolean first=true;
            for(long s:STRING_SEEDS) { Address at=a(s); for(Reference r:currentProgram.getReferenceManager().getReferencesTo(at)) { if(!first)o.println(","); first=false; Function owner=currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress()); o.print("{\"string_va\":"+esc(hex(at))+",\"string_file_offset\":"+esc(file(at))+",\"from_va\":"+esc(hex(r.getFromAddress()))+",\"from_file_offset\":"+esc(file(r.getFromAddress()))+",\"reference_type\":"+esc(r.getReferenceType().toString())+",\"owner_entry_va\":"+esc(owner==null?null:hex(owner.getEntryPoint()))+"}"); } }
            o.println("],\"tail_direct_reference_sites\":[");
            first=true; int count=0; InstructionIterator ins=currentProgram.getListing().getInstructions(true);
            while(ins.hasNext()) { Instruction i=ins.next(); for(Reference r:i.getReferencesFrom()) { Address to=r.getToAddress(); if(to!=null && to.getOffset()>=TAIL_START && to.getOffset()<=TAIL_END) { if(!first)o.println(","); first=false; Function owner=currentProgram.getFunctionManager().getFunctionContaining(i.getAddress()); o.print("{\"from_va\":"+esc(hex(i.getAddress()))+",\"from_file_offset\":"+esc(file(i.getAddress()))+",\"to_va\":"+esc(hex(to))+",\"to_file_offset\":"+esc(file(to))+",\"mnemonic\":"+esc(i.getMnemonicString())+",\"reference_type\":"+esc(r.getReferenceType().toString())+",\"owner_entry_va\":"+esc(owner==null?null:hex(owner.getEntryPoint()))+"}"); if(++count>=500) break; } } if(count>=500) break; }
            o.println("],\"tail_reference_limit\":"+count+",\"limitations\":[\"Only direct Ghidra references are listed; raw constants, computed pointers, data-table entries and runtime mappings can be absent.\",\"Pseudocode/function types are Ghidra inferences, not runtime evidence.\"]}");
        } finally { d.dispose(); }
    }
}
