// Phase 5 offline evidence exporter. Logical VA mapping is a hypothesis only.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;

public class ExportPhase5EventLifecycle extends GhidraScript {
    private static final long[] FUNCTIONS = {0x25668,0x63b0,0x1c9c4,0xcc2c,0x1e234,0x6134,0x2d31c,0x6378,0x25984,0x25a38,0x21170};
    private static final long[] VALUES = {0x100,0x108,0x5025};
    private static final long BIAS = 0x200;
    private static String q(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""; }
    private static String va(Address a) { return String.format("0x%08x", a.getOffset()); }
    private static String fo(long v) { return String.format("0x%06x", v + BIAS); }
    private static void array(PrintWriter o, List<String> xs) { o.print("["); for (int i=0;i<xs.size();i++) { if(i>0)o.print(","); o.print(q(xs.get(i))); } o.print("]"); }
    private List<String> calls(Function f) { List<String> r=new ArrayList<>(); InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true); while(it.hasNext()) { Instruction i=it.next(); if(i.getFlowType().isCall()) for(Address to:i.getFlows()) r.add(va(i.getAddress())+"->"+va(to)); } return r; }
    private List<String> incoming(Address a) { List<String> r=new ArrayList<>(); for(Reference x:currentProgram.getReferenceManager().getReferencesTo(a)) r.add(va(x.getFromAddress())+"->"+va(x.getToAddress())+":"+x.getReferenceType()); return r; }

    @Override public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("export directory required");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        File pseudo = new File(root,"pseudocode"); pseudo.mkdirs();
        DecompInterface decomp = new DecompInterface(); decomp.openProgram(currentProgram);
        try(PrintWriter o=new PrintWriter(new FileWriter(new File(root,"phase5_event_graph.json")))) {
            o.println("{\"mapping\":\"file offset = logical VA + 0x200; hypothesis only\",\"scalar_hits\":[");
            boolean first=true; InstructionIterator all=currentProgram.getListing().getInstructions(true);
            while(all.hasNext()) { Instruction i=all.next(); for(int operand=0;operand<i.getNumOperands();operand++) for(Object object:i.getOpObjects(operand)) { if(!(object instanceof Scalar)) continue; long v=((Scalar)object).getUnsignedValue(); boolean wanted=false; for(long candidate:VALUES) if(v==candidate) wanted=true; if(!wanted) continue; if(!first)o.println(","); first=false; Function f=currentProgram.getFunctionManager().getFunctionContaining(i.getAddress()); o.print("{\"value\":"+q(String.format("0x%x",v))+",\"instruction_va\":"+q(va(i.getAddress()))+",\"instruction_file_offset\":"+q(fo(i.getAddress().getOffset()))+",\"instruction\":"+q(i.toString())+",\"function_entry_va\":"+q(f==null?"none":va(f.getEntryPoint()))+"}"); } }
            o.println("],\"functions\":["); first=true;
            for(long target:FUNCTIONS) { Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(target); Function f=currentProgram.getFunctionManager().getFunctionContaining(a); if(!first)o.println(","); first=false; o.print("{\"requested_va\":"+q(va(a))+",\"requested_file_offset\":"+q(fo(target))+",\"incoming_references\":"); array(o,incoming(a)); if(f==null){o.print(",\"status\":\"no_containing_function\"}");continue;} DecompileResults result=decomp.decompileFunction(f,90,monitor); String stem=String.format("%06x",f.getEntryPoint().getOffset()+BIAS); try(PrintWriter c=new PrintWriter(new FileWriter(new File(pseudo,stem+".c")))){c.println("/* requested VA "+va(a)+", containing VA "+va(f.getEntryPoint())+" */");c.println(result.getDecompiledFunction()==null?"/* no pseudocode */":result.getDecompiledFunction().getC());} o.print(",\"entry_va\":"+q(va(f.getEntryPoint()))+",\"entry_file_offset\":"+q(fo(f.getEntryPoint().getOffset()))+",\"calls\":");array(o,calls(f));o.print(",\"pseudocode_file\":"+q("pseudocode/"+stem+".c")+",\"decompile_complete\":"+(result.decompileCompleted()?"true":"false")+"}"); }
            o.println("],\"limitations\":[\"Scalar hits do not establish message production or runtime ordering.\",\"Decompiler function types are not source-level ABI proof.\"]}");
        } finally {decomp.dispose();}
    }
}
